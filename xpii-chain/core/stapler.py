import os
import hashlib
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
        self.namespaces = {
            'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
            'cp': 'http://schemas.openxmlformats.org/package/2006/metadata/core-properties',
            'dc': 'http://purl.org/dc/elements/1.1/',
            'dcterms': 'http://purl.org/dc/terms/',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
        }

    def unpack(self, docx_path):
        """Phase 1: Unpack the .docx (ZIP) archive."""
        if os.path.exists(self.work_dir):
            shutil.rmtree(self.work_dir)
        os.makedirs(self.work_dir)
        
        with zipfile.ZipFile(docx_path, 'r') as zip_ref:
            zip_ref.extractall(self.work_dir)
        print(f"Unpacked {docx_path} to {self.work_dir}")

    def _session_to_rsid(self, session_id):
        """Derive a deterministic 8-character hex RSID from the session identifier."""
        digest = hashlib.sha256(session_id.encode('utf-8')).hexdigest()
        return digest[:8].upper()

    def inject_metadata(self, author="XPII-CHAIN", session_id=None):
        """Phase 2: Targeted XML manipulation for metadata embedding."""
        if not session_id:
            session_id = datetime.now().strftime("%Y%m%d%H%M%S")

        rsid_value = self._session_to_rsid(session_id)

        # 1. Edit Core Properties (Author, Last Modified)
        core_props_path = os.path.join(self.work_dir, 'docProps', 'core.xml')
        if os.path.exists(core_props_path):
            tree = ET.parse(core_props_path)
            root = tree.getroot()

            # Update creator
            creator = root.find('dc:creator', self.namespaces)
            if creator is not None:
                creator.text = author
            else:
                creator = ET.SubElement(root, '{http://purl.org/dc/elements/1.1/}creator')
                creator.text = author

            # Embed session identifier and cryptographic provenance hash
            desc = root.find('dc:description', self.namespaces)
            if desc is None:
                desc = ET.SubElement(root, '{http://purl.org/dc/elements/1.1/}description')
            desc.text = f"XPII-CHAIN-PROVENANCE: {session_id} | SHA256-RSID: {rsid_value}"

            # Update last modified timestamp
            modified = root.find('dcterms:modified', self.namespaces)
            if modified is None:
                modified = ET.SubElement(
                    root,
                    '{http://purl.org/dc/terms/}modified',
                    attrib={'{http://www.w3.org/2001/XMLSchema-instance}type': 'dcterms:W3CDTF'}
                )
            modified.text = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

            tree.write(core_props_path, encoding='UTF-8', xml_declaration=True)

        # 2. Inject RSID (Revision Save ID) into word/settings.xml
        settings_path = os.path.join(self.work_dir, 'word', 'settings.xml')
        if os.path.exists(settings_path):
            W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
            tree = ET.parse(settings_path)
            root = tree.getroot()

            rsids_tag = f'{{{W}}}rsids'
            rsid_tag = f'{{{W}}}rsid'

            rsids = root.find(rsids_tag)
            if rsids is None:
                rsids = ET.SubElement(root, rsids_tag)

            # Check whether this RSID is already present to avoid duplicates
            existing = {el.get(f'{{{W}}}val') for el in rsids.findall(rsid_tag)}
            if rsid_value not in existing:
                rsid_el = ET.SubElement(rsids, rsid_tag)
                rsid_el.set(f'{{{W}}}val', rsid_value)

            tree.write(settings_path, encoding='UTF-8', xml_declaration=True)

        print(f"Injected metadata for session {session_id} (RSID: {rsid_value})")

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

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 3:
        input_path, output_path = sys.argv[1], sys.argv[2]
        stapler = XPIIStapler()
        stapler.unpack(input_path)
        stapler.inject_metadata(author="XPII-CHAIN-PROVENANCE")
        stapler.pack(output_path)
    else:
        print("Usage: python stapler.py <input.docx> <output.docx>")
