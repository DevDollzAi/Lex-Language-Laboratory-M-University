import hashlib
import os
import zipfile
import shutil
import lxml.etree as ET
from datetime import datetime

class XPIIStapler:
    """
    Deterministic Provenance Stapler (XPII CHAIN)
    Implements the Unpack-Edit-Pack pipeline for OOXML metadata embedding.
    """
    
    def __init__(self, work_dir="temp_unpack"):
        self.work_dir = work_dir
        self.provenance_fingerprint = None
        self.file_hash = None
        self.namespaces = {
            'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
            'cp': 'http://schemas.openxmlformats.org/package/2006/metadata/core-properties',
            'dc': 'http://purl.org/dc/elements/1.1/',
            'dcterms': 'http://purl.org/dc/terms/',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
        }

    def _compute_sha256(self, file_path):
        """Compute SHA-256 hash of a file."""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    def unpack(self, docx_path):
        """Phase 1: Unpack the .docx (ZIP) archive."""
        if os.path.exists(self.work_dir):
            shutil.rmtree(self.work_dir)
        os.makedirs(self.work_dir)
        
        with zipfile.ZipFile(docx_path, 'r') as zip_ref:
            zip_ref.extractall(self.work_dir)
        print(f"Unpacked {docx_path} to {self.work_dir}")

    def inject_metadata(self, author="XPII-CHAIN", session_id=None):
        """Phase 2: Targeted XML manipulation for metadata embedding."""
        if not session_id:
            session_id = datetime.now().strftime("%Y%m%d%H%M%S")

        # Derive a deterministic fingerprint from author + session_id
        fingerprint = hashlib.sha256(f"{author}:{session_id}".encode()).hexdigest()
        self.provenance_fingerprint = fingerprint

        # 1. Edit Core Properties (Author, Last Modified)
        core_props_path = os.path.join(self.work_dir, 'docProps', 'core.xml')
        if os.path.exists(core_props_path):
            tree = ET.parse(core_props_path)
            root = tree.getroot()
            
            # Update creator
            creator = root.find('dc:creator', self.namespaces)
            if creator is not None:
                creator.text = author
            
            # Add custom session identifier in description or keywords
            desc = root.find('dc:description', self.namespaces)
            if desc is None:
                desc = ET.SubElement(root, '{http://purl.org/dc/elements/1.1/}description')
            desc.text = f"XPII-CHAIN-PROVENANCE: {session_id} | SHA-256: {fingerprint}"
            
            tree.write(core_props_path, encoding='UTF-8', xml_declaration=True)

        # 2. Inject RSID (Revision Save ID) into settings.xml
        settings_path = os.path.join(self.work_dir, 'word', 'settings.xml')
        if os.path.exists(settings_path):
            tree = ET.parse(settings_path)
            root = tree.getroot()

            w_ns = self.namespaces['w']
            rsids = root.find(f'{{{w_ns}}}rsids')
            if rsids is None:
                rsids = ET.SubElement(root, f'{{{w_ns}}}rsids')

            # Use the first 8 hex characters of the fingerprint as the RSID value
            rsid_value = fingerprint[:8].upper()
            existing = any(
                elem.get(f'{{{w_ns}}}val') == rsid_value
                for elem in rsids.findall(f'{{{w_ns}}}rsid')
            )
            if not existing:
                rsid_elem = ET.SubElement(rsids, f'{{{w_ns}}}rsid')
                rsid_elem.set(f'{{{w_ns}}}val', rsid_value)

            tree.write(settings_path, encoding='UTF-8', xml_declaration=True)

        # 3. Touch document.xml to record the edit
        doc_xml_path = os.path.join(self.work_dir, 'word', 'document.xml')
        if os.path.exists(doc_xml_path):
            tree = ET.parse(doc_xml_path)
            tree.write(doc_xml_path, encoding='UTF-8', xml_declaration=True)
            
        print(f"Injected metadata for session {session_id} | SHA-256: {fingerprint}")
        return fingerprint

    def pack(self, output_path):
        """Phase 3: Repack and auto-repair sequence."""
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
            for root, dirs, files in os.walk(self.work_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, self.work_dir)
                    zip_ref.write(file_path, arcname)
        
        # Compute final file hash and store it
        self.file_hash = self._compute_sha256(output_path)

        # Cleanup
        shutil.rmtree(self.work_dir)
        print(f"Packed document to {output_path} | SHA-256: {self.file_hash}")
        return self.file_hash

    def verify(self, docx_path):
        """Verify a stapled document by reading its embedded provenance metadata."""
        result = {"status": "UNVERIFIED", "session_id": None, "sha256": None, "author": None}

        try:
            with zipfile.ZipFile(docx_path, 'r') as zf:
                if 'docProps/core.xml' not in zf.namelist():
                    result["status"] = "NO_METADATA"
                    return result

                with zf.open('docProps/core.xml') as f:
                    tree = ET.parse(f)
                    root = tree.getroot()

                    creator = root.find('dc:creator', self.namespaces)
                    if creator is not None:
                        result["author"] = creator.text

                    desc = root.find('dc:description', self.namespaces)
                    if desc is not None and desc.text and "XPII-CHAIN-PROVENANCE:" in desc.text:
                        # Parse "XPII-CHAIN-PROVENANCE: <session_id> | SHA-256: <hash>"
                        parts = desc.text.split("|")
                        session_part = parts[0].replace("XPII-CHAIN-PROVENANCE:", "").strip()
                        result["session_id"] = session_part
                        if len(parts) > 1 and "SHA-256:" in parts[1]:
                            result["sha256"] = parts[1].replace("SHA-256:", "").strip()
                        result["status"] = "VERIFIED"
                    else:
                        result["status"] = "NO_PROVENANCE"
        except (zipfile.BadZipFile, ET.XMLSyntaxError) as e:
            result["status"] = f"ERROR: {e}"

        return result

if __name__ == "__main__":
    # Example usage
    stapler = XPIIStapler()
    # stapler.unpack("input.docx")
    # stapler.inject_metadata(author="Axiom Hive")
    # stapler.pack("output_stapled.docx")
    # print(stapler.verify("output_stapled.docx"))
