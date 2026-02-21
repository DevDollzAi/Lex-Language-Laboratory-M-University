import os
import zipfile
import shutil
import hashlib
import lxml.etree as ET
from datetime import datetime, timezone

class XPIIStapler:
    """
    Deterministic Provenance Stapler (XPII CHAIN)
    Implements the Unpack-Edit-Pack pipeline for OOXML metadata embedding.
    """

    XPII_HASH_KEY = "XPII-CHAIN-SHA256"
    XPII_SESSION_KEY = "XPII-CHAIN-PROVENANCE"
    _HASH_CHUNK_SIZE = 65536  # 64 KB read buffer for SHA-256 streaming

    def __init__(self, work_dir="temp_unpack"):
        self.work_dir = work_dir
        self.namespaces = {
            'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
            'cp': 'http://schemas.openxmlformats.org/package/2006/metadata/core-properties',
            'dc': 'http://purl.org/dc/elements/1.1/',
            'dcterms': 'http://purl.org/dc/terms/',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
        }
        self._source_hash = None

    # ------------------------------------------------------------------
    # Phase 0: Cryptographic hash of source document
    # ------------------------------------------------------------------

    def hash_file(self, docx_path):
        """Compute the SHA-256 digest of the source .docx file."""
        sha256 = hashlib.sha256()
        with open(docx_path, 'rb') as fh:
            for chunk in iter(lambda: fh.read(self._HASH_CHUNK_SIZE), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    # ------------------------------------------------------------------
    # Phase 1: Unpack
    # ------------------------------------------------------------------

    def unpack(self, docx_path):
        """Phase 1: Unpack the .docx (ZIP) archive and capture its hash."""
        if os.path.exists(self.work_dir):
            shutil.rmtree(self.work_dir)
        os.makedirs(self.work_dir)

        self._source_hash = self.hash_file(docx_path)

        with zipfile.ZipFile(docx_path, 'r') as zip_ref:
            zip_ref.extractall(self.work_dir)
        print(f"Unpacked {docx_path} to {self.work_dir}")
        print(f"Source SHA-256: {self._source_hash}")
        return self._source_hash

    # ------------------------------------------------------------------
    # Phase 2: Inject metadata
    # ------------------------------------------------------------------

    def inject_metadata(self, author="XPII-CHAIN", session_id=None):
        """Phase 2: Targeted XML manipulation for metadata embedding.

        Returns the SHA-256 hash of the original source document so callers
        can display or record the provenance fingerprint.
        """
        if not session_id:
            session_id = datetime.now().strftime("%Y%m%d%H%M%S")

        source_hash = self._source_hash or "UNKNOWN"

        # 1. Edit Core Properties (docProps/core.xml)
        core_props_path = os.path.join(self.work_dir, 'docProps', 'core.xml')
        if os.path.exists(core_props_path):
            tree = ET.parse(core_props_path)
            root = tree.getroot()

            # Update or create dc:creator
            creator = root.find('dc:creator', self.namespaces)
            if creator is None:
                creator = ET.SubElement(root, '{http://purl.org/dc/elements/1.1/}creator')
            creator.text = author

            # Update or create dc:description with provenance session tag
            desc = root.find('dc:description', self.namespaces)
            if desc is None:
                desc = ET.SubElement(root, '{http://purl.org/dc/elements/1.1/}description')
            desc.text = (
                f"{self.XPII_SESSION_KEY}: {session_id} | "
                f"{self.XPII_HASH_KEY}: {source_hash}"
            )

            # Update dcterms:modified timestamp
            modified = root.find('dcterms:modified', self.namespaces)
            if modified is None:
                modified = ET.SubElement(
                    root,
                    '{http://purl.org/dc/terms/}modified',
                    {'{http://www.w3.org/2001/XMLSchema-instance}type': 'dcterms:W3CDTF'}
                )
            modified.text = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

            tree.write(core_props_path, encoding='UTF-8', xml_declaration=True)

        # 2. Inject RSID (Revision Save ID) into word/settings.xml
        settings_path = os.path.join(self.work_dir, 'word', 'settings.xml')
        if os.path.exists(settings_path):
            for prefix, uri in self.namespaces.items():
                ET.register_namespace(prefix, uri)
            tree = ET.parse(settings_path)
            root = tree.getroot()

            W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
            rsids_tag = f'{{{W}}}rsids'
            rsid_tag = f'{{{W}}}rsid'
            w_val = f'{{{W}}}val'

            rsids_elem = root.find(rsids_tag)
            if rsids_elem is None:
                rsids_elem = ET.SubElement(root, rsids_tag)

            # RSID values are 8 upper-case hex characters (OOXML spec §2.8.1).
            # We derive a deterministic value from the session_id so the same
            # session always produces the same RSID, enabling reproducibility.
            rsid_val = hashlib.sha256(session_id.encode()).hexdigest()[:8].upper()

            # Only add the RSID entry if it is not already present
            existing = {e.get(w_val) for e in rsids_elem.findall(rsid_tag)}
            if rsid_val not in existing:
                ET.SubElement(rsids_elem, rsid_tag, {w_val: rsid_val})

            tree.write(settings_path, encoding='UTF-8', xml_declaration=True)

        print(f"Injected metadata for session {session_id}")
        print(f"Provenance hash: {source_hash}")
        return source_hash

    # ------------------------------------------------------------------
    # Phase 3: Pack
    # ------------------------------------------------------------------

    def pack(self, output_path):
        """Phase 3: Repack and auto-repair sequence."""
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
            for root, dirs, files in os.walk(self.work_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, self.work_dir)
                    zip_ref.write(file_path, arcname)

        # Cleanup
        shutil.rmtree(self.work_dir)
        print(f"Packed document to {output_path}")

    # ------------------------------------------------------------------
    # Verification
    # ------------------------------------------------------------------

    def verify(self, stapled_docx_path):
        """Verify the provenance metadata embedded in a stapled .docx.

        Extracts the session and hash values from docProps/core.xml and
        returns a dict with the embedded fields, or raises ValueError if
        no XPII provenance marker is found.
        """
        with zipfile.ZipFile(stapled_docx_path, 'r') as zip_ref:
            if 'docProps/core.xml' not in zip_ref.namelist():
                raise ValueError("No docProps/core.xml found in the document.")
            with zip_ref.open('docProps/core.xml') as fh:
                tree = ET.parse(fh)

        root = tree.getroot()
        desc = root.find('dc:description', self.namespaces)
        if desc is None or desc.text is None:
            raise ValueError("No XPII provenance marker found in this document.")

        raw = desc.text
        if self.XPII_SESSION_KEY not in raw:
            raise ValueError("No XPII provenance marker found in this document.")

        result = {'raw': raw}
        for part in raw.split(' | '):
            if ': ' in part:
                key, value = part.split(': ', 1)
                result[key.strip()] = value.strip()

        creator = root.find('dc:creator', self.namespaces)
        result['author'] = creator.text if creator is not None else 'Unknown'

        modified = root.find('dcterms:modified', self.namespaces)
        result['modified'] = modified.text if modified is not None else 'Unknown'

        return result


if __name__ == "__main__":
    # Example usage
    stapler = XPIIStapler()
    # stapler.unpack("input.docx")
    # stapler.inject_metadata(author="Axiom Hive")
    # stapler.pack("output_stapled.docx")
