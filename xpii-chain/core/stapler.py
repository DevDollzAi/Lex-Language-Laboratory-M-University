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

    def inject_metadata(self, author="XPII-CHAIN", session_id=None):
        """Phase 2: Targeted XML manipulation for metadata embedding."""
        if not session_id:
            session_id = datetime.now().strftime("%Y%m%d%H%M%S")
            
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
            desc.text = f"XPII-CHAIN-PROVENANCE: {session_id}"
            
            tree.write(core_props_path, encoding='UTF-8', xml_declaration=True)

        # 2. Inject RSID (Revision Save ID) into document.xml
        doc_xml_path = os.path.join(self.work_dir, 'word', 'document.xml')
        if os.path.exists(doc_xml_path):
            tree = ET.parse(doc_xml_path)
            root = tree.getroot()
            
            # Find the rsids section or create it
            settings_path = os.path.join(self.work_dir, 'word', 'settings.xml')
            # (Simplified for now: we'll just add a comment or custom tag if possible)
            # In a real scenario, we'd manipulate <w:rsids>
            
            tree.write(doc_xml_path, encoding='UTF-8', xml_declaration=True)
            
        print(f"Injected metadata for session {session_id}")

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
    # Example usage
    stapler = XPIIStapler()
    # stapler.unpack("input.docx")
    # stapler.inject_metadata(author="Axiom Hive")
    # stapler.pack("output_stapled.docx")
