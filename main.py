import os
import shutil
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from typing import List, Dict, Any

import pandas as pd
import rarfile
from openpyxl.styles import PatternFill, Font
from tqdm import tqdm

# --- Configuration ---

# The namespace is crucial for finding elements in the CT-e XML file.
XML_NAMESPACE = {"ns": "http://www.portalfiscal.inf.br/cte"}

# Defines the exact order and names of the columns for the Excel file.
# Headers in parentheses like "(CTe)" are treated as visual separators.
EXCEL_HEADERS: List[str] = [
    "(CTe)", "chv_cte_Id", "(ide)", "ide_cUF", "ide_cCT", "ide_CFOP", "ide_natOp",
    "ide_mod", "ide_serie", "ide_nCT", "ide_dhEmi", "ide_tpImp", "ide_tpEmis",
    "ide_cDV", "ide_tpAmb", "ide_tpCTe", "ide_procEmi", "ide_verProc",
    "ide_cMunEnv", "ide_xMunEnv", "ide_UFEnv", "ide_modal", "ide_tpServ",
    "ide_cMunIni", "ide_xMunIni", "ide_UFIni", "ide_cMunFim", "ide_xMunFim",
    "ide_UFFim", "ide_retira", "ide_indIEToma", "(ide_toma3)", "ide_toma3_toma",
    "(ide_toma4)", "ide_toma4_toma", "ide_toma4_CNPJ", "ide_toma4_IE",
    "ide_toma4_xNome", "ide_toma4_xFant", "ide_toma4_fone",
    "(ide_toma4_enderToma)", "ide_toma4_enderToma_xLgr",
    "ide_toma4_enderToma_nro", "ide_toma4_enderToma_xBairro",
    "ide_toma4_enderToma_cMun", "ide_toma4_enderToma_xMun",
    "ide_toma4_enderToma_CEP", "ide_toma4_enderToma_UF",
    "ide_toma4_enderToma_cPais", "ide_toma4_enderToma_xPais", "ide_toma4_email",
    "(compl)", "(compl_Entrega)", "compl_Entrega_tpPer", "compl_Entrega_dProg",
    "compl_Entrega_tpHor", "compl_origCalc", "compl_destCalc", "compl_xObs",
    "(emit)", "emit_CNPJ", "emit_IE", "emit_xNome", "emit_xFant",
    "(emit_enderEmit)", "emit_enderEmit_xLgr",
    "emit_enderEmit_nro", "emit_enderEmit_xCpl", "emit_enderEmit_xBairro",
    "emit_enderEmit_cMun", "emit_enderEmit_xMun", "emit_enderEmit_CEP",
    "emit_enderEmit_UF", "emit_enderEmit_fone", "(rem)", "rem_CNPJ", "rem_CPF",
    "rem_IE", "rem_xNome", "rem_xFant", "rem_fone", "(rem_enderReme)",
    "rem_enderReme_xLgr", "rem_enderReme_nro", "rem_enderReme_xBairro",
    "rem_enderReme_cMun", "rem_enderReme_xMun", "rem_enderReme_CEP",
    "rem_enderReme_UF", "rem_enderReme_cPais", "rem_enderReme_xPais",
    "rem_email", "(exped)", "exped_CNPJ", "exped_IE", "exped_xNome",
    "exped_fone", "(exped_enderExped)", "exped_enderExped_xLgr",
    "exped_enderExped_nro", "exped_enderExped_xBairro",
    "exped_enderExped_cMun", "exped_enderExped_xMun", "exped_enderExped_CEP",
    "exped_enderExped_UF", "exped_enderExped_cPais", "exped_enderExped_xPais",
    "exped_email", "(receb)", "receb_CNPJ", "receb_CPF", "receb_IE", "receb_xNome",
    "receb_fone", "(receb_enderReceb)", "receb_enderReceb_xLgr",
    "receb_enderReceb_nro", "receb_enderReceb_xBairro",
    "receb_enderReceb_cMun", "receb_enderReceb_xMun", "receb_enderReceb_CEP",
    "receb_enderReceb_UF", "receb_enderReceb_cPais", "receb_enderReceb_xPais",
    "receb_email", "(dest)", "dest_CNPJ", "dest_CPF", "dest_IE", "dest_xNome",
    "dest_fone", "(dest_enderDest)", "dest_enderDest_xLgr",
    "dest_enderDest_nro", "dest_enderDest_xBairro", "dest_enderDest_cMun",
    "dest_enderDest_xMun", "dest_enderDest_CEP", "dest_enderDest_UF",
    "dest_enderDest_cPais", "dest_enderDest_xPais", "dest_email", "(vPrest)",
    "vPrest_vTPrest", "vPrest_vRec", "(vPrest_Comp)", "vPrest_xNome", "vPrest_vComp",
    "(imp)", "imp_CST", "imp_vBC", "imp_pICMS", "imp_vICMS",
    "imp_vBCSTRet", "imp_vICMSSTRet", "imp_pICMSSTRet", "(imp_ICMSOutraUF)",
    "imp_ICMSOutraUF_CST", "imp_ICMSOutraUF_vBCOutraUF",
    "imp_ICMSOutraUF_pICMSOutraUF", "imp_ICMSOutraUF_vICMSOutraUF",
    "imp_vTotTrib", "imp_infAdFisco", "(infCTeNorm)",
    "(infCTeNorm_infCarga)", "infCTeNorm_infCarga_vCarga",
    "infCTeNorm_infCarga_proPred", "(infCTeNorm_infCteSub)",
    "infCTeNorm_infCteSub_chCte", "infCTeNorm_infCteSub_indAlteraToma",
    "(infCTeNorm_infServVinc)", "(infCTeNorm_infServVinc_infCTeMultimodal)",
    "infCTeNorm_infServVinc_infCTeMultimodal_chCTeMultimodal",
    "(infCteComp)", "infCteComp_chCTe"
]

# --- Class Definitions ---

class ArchiveHandler:
    """
    Handles the recursive extraction of .rar and .zip archives and
    discovery of XML files within a temporary directory.
    """

    def __init__(self, archive_path: str):
        if not os.path.exists(archive_path):
            raise FileNotFoundError(f"Archive not found at: {archive_path}")
        self.archive_path = archive_path
        self.temp_dir = tempfile.mkdtemp(prefix="cte_extraction_")

    def _extract_recursive(self):
        """
        Continuously scans the temporary directory for .rar and .zip files
        and extracts them until no archives remain.
        """
        while True:
            archives_found = False
            for root, _, files in os.walk(self.temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    extract_path = os.path.dirname(file_path)
                    
                    try:
                        if file.lower().endswith(".rar"):
                            with rarfile.RarFile(file_path) as rf:
                                rf.extractall(path=extract_path)
                            os.remove(file_path)
                            archives_found = True
                        elif file.lower().endswith(".zip"):
                            with zipfile.ZipFile(file_path) as zf:
                                zf.extractall(path=extract_path)
                            os.remove(file_path)
                            archives_found = True
                    except Exception as e:
                        print(f"Warning: Failed to extract '{file}'. Reason: {e}")
                        # Rename or remove to avoid infinite loop
                        os.rename(file_path, file_path + ".failed")
            
            if not archives_found:
                break

    def extract_all(self):
        """
        Extracts the initial .rar file and then recursively extracts all
        nested archives.
        """
        print(f"Extracting main archive: {os.path.basename(self.archive_path)}...")
        try:
            with rarfile.RarFile(self.archive_path) as rf:
                rf.extractall(path=self.temp_dir)
            
            print("Scanning for nested archives...")
            self._extract_recursive()
        except rarfile.Error as e:
            raise RuntimeError(f"Failed to extract RAR file. Ensure 'unrar' is installed. Details: {e}")

    def find_xml_files(self) -> List[str]:
        """
        Recursively finds all .xml files in the temporary directory.
        """
        xml_files = []
        for root, _, files in os.walk(self.temp_dir):
            for file in files:
                if file.lower().endswith(".xml"):
                    xml_files.append(os.path.join(root, file))
        return xml_files

    def cleanup(self):
        """Deletes the temporary extraction directory."""
        if os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except OSError as e:
                print(f"Warning: Could not clean up temp directory {self.temp_dir}: {e}")


class XMLParser:
    """
    Parses a CT-e XML file, handling namespaces, extracting data,
    and managing 1-to-N relationships for components.
    """

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.namespace = XML_NAMESPACE
        try:
            self.tree = ET.parse(file_path)
            self.root = self.tree.getroot()
        except ET.ParseError as e:
            raise ValueError(f"Error parsing XML file: {e}")

    def extract_data(self, headers: List[str]) -> List[Dict[str, str]]:
        """
        Extracts data for each header from the XML file, generating multiple
        rows if multiple 'Comp' tags are found in 'vPrest'.

        Args:
            headers: A list of column headers to extract.

        Returns:
            A list of dictionaries, where each dictionary represents a row.
        """
        base_data = {}
        inf_cte_node = self.root.find(".//ns:infCte", self.namespace)
        if inf_cte_node is None:
            # Warning suppressed for batch processing cleanliness, returning empty row
            return [{header: "" for header in headers}]

        # Special handling for the CTe key, which is an attribute
        base_data["chv_cte_Id"] = inf_cte_node.get("Id", "").replace("CTe", "")

        # Pre-calculate ICMS child (Critical Rule 2)
        # Finds the first child of <imp><ICMS>, which could be ICMS00, ICMS20, ICMSOutraUF, etc.
        icms_node = inf_cte_node.find("ns:imp/ns:ICMS", self.namespace)
        active_icms_child = None
        if icms_node is not None and len(icms_node) > 0:
            active_icms_child = icms_node[0]

        icms_generic_fields = ["imp_CST", "imp_vBC", "imp_pICMS", "imp_vICMS", 
                               "imp_vBCSTRet", "imp_vICMSSTRet", "imp_pICMSSTRet"]
        icms_outra_uf_fields = ["imp_ICMSOutraUF_CST", "imp_ICMSOutraUF_vBCOutraUF", 
                                "imp_ICMSOutraUF_pICMSOutraUF", "imp_ICMSOutraUF_vICMSOutraUF"]

        # Extract common fields (everything except specific component data)
        for header in headers:
            if header.startswith("(") or header == "chv_cte_Id":
                continue  # Skip separators and already processed keys

            # Skip component specific fields for now, they are handled in the loop below
            if header in ["vPrest_xNome", "vPrest_vComp"]:
                continue

            val = ""
            if header in icms_generic_fields:
                # Search inside the active ICMS child (e.g., ICMS00) for the specific tag (e.g., CST)
                if active_icms_child is not None:
                    tag = header.split("_")[1]
                    el = active_icms_child.find(f"ns:{tag}", self.namespace)
                    val = el.text if el is not None else ""
            elif header in icms_outra_uf_fields:
                # Specific handling for ICMSOutraUF group
                if active_icms_child is not None and "ICMSOutraUF" in active_icms_child.tag:
                    tag = header.replace("imp_ICMSOutraUF_", "")
                    el = active_icms_child.find(f"ns:{tag}", self.namespace)
                    val = el.text if el is not None else ""
            else:
                # Standard logic for all other fields
                path_parts = header.split("_")
                xpath = ".//" + "/".join([f"ns:{part}" for part in path_parts])
                element = inf_cte_node.find(xpath, self.namespace)
                val = element.text if element is not None else ""
            
            base_data[header] = val
            
        # Handle 1-to-N for Components (vPrest/Comp)
        rows = []
        vprest_node = inf_cte_node.find(".//ns:vPrest", self.namespace)
        comps = vprest_node.findall("ns:Comp", self.namespace) if vprest_node is not None else []

        if comps:
            for comp in comps:
                row = base_data.copy()
                x_nome = comp.find("ns:xNome", self.namespace)
                v_comp = comp.find("ns:vComp", self.namespace)
                
                row["vPrest_xNome"] = x_nome.text if x_nome is not None else ""
                row["vPrest_vComp"] = v_comp.text if v_comp is not None else ""
                rows.append(row)
        else:
            # If no components are found, create one row with empty component fields
            row = base_data.copy()
            row["vPrest_xNome"] = ""
            row["vPrest_vComp"] = ""
            rows.append(row)

        return rows


class ExcelExporter:
    """
    Aggregates data and exports it to a styled Excel (.xlsx) file using pandas.
    """

    def __init__(self, data: List[Dict[str, Any]], headers: List[str]):
        self.data = data
        self.headers = headers

    def export(self, output_filename: str):
        """
        Creates and saves the styled Excel file.
        """
        if not self.data:
            print("No data to export.")
            return

        print(f"Generating Excel file: {output_filename}...")
        
        # Create DataFrame and ensure column order
        df = pd.DataFrame(self.data)
        # Reindex to ensure all columns are present and in order, filling missing with ""
        df = df.reindex(columns=self.headers, fill_value="")

        with pd.ExcelWriter(output_filename, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='CTe Data')
            
            # Apply styling using openpyxl
            workbook = writer.book
            worksheet = writer.sheets['CTe Data']
            
            gray_fill = PatternFill(start_color="D3D3D3", end_color="D3D3D3", fill_type="solid")
            bold_font = Font(bold=True)

            # Iterate over columns to apply styles
            for col_idx, header_text in enumerate(self.headers, 1):
                # Style Header
                cell = worksheet.cell(row=1, column=col_idx)
                cell.font = bold_font
                
                # Check if it is a separator column
                if header_text.startswith("(") and header_text.endswith(")"):
                    # Apply gray fill to the entire column (header + data)
                    # Note: Iterating rows in openpyxl can be slow for huge datasets, 
                    # but is necessary for cell-specific styling.
                    for row in worksheet.iter_rows(min_row=1, max_row=worksheet.max_row, min_col=col_idx, max_col=col_idx):
                        for cell in row:
                            cell.fill = gray_fill


class AppController:
    """
    Orchestrates the conversion process from XML to Excel.
    """

    def __init__(self, input_dir: str = "files"):
        self.input_dir = input_dir
        self._ensure_input_dir()

    def _ensure_input_dir(self):
        """Ensures the input directory exists."""
        if not os.path.exists(self.input_dir):
            os.makedirs(self.input_dir)
            print(f"Created directory: '{self.input_dir}/'")
            print(f"Please place your .rar file inside it and run the script again.")
            exit()

    def run(self):
        """Main application loop."""
        print("--- CT-e XML to Excel Converter ---")
        
        try:
            rar_filename = input(f"Enter the name of the .rar file (must be in '{self.input_dir}/' folder): ")
            rar_path = os.path.join(self.input_dir, rar_filename)

            if not os.path.exists(rar_path):
                print(f"\nError: File '{rar_filename}' not found in the '{self.input_dir}/' directory.")
                return

            # 1. Extract Archives
            archive_handler = ArchiveHandler(rar_path)
            archive_handler.extract_all()

            # 2. Find XMLs
            xml_files = archive_handler.find_xml_files()
            print(f"Total XML files found: {len(xml_files)}")

            # 3. Batch Process with Progress Bar
            all_data = []
            for xml_file in tqdm(xml_files, desc="Processing XMLs", unit="file"):
                try:
                    parser = XMLParser(xml_file)
                    rows = parser.extract_data(EXCEL_HEADERS)
                    all_data.extend(rows)
                except Exception as e:
                    # Log error but continue processing other files
                    # In a real app, you might write this to an error.log
                    pass

            # 4. Export to Excel
            output_filename = f"{os.path.splitext(rar_filename)[0]}.xlsx"
            exporter = ExcelExporter(all_data, EXCEL_HEADERS)
            exporter.export(output_filename)

            # 5. Cleanup
            archive_handler.cleanup()
            print(f"\nSuccess! Data has been converted to '{output_filename}'")

        except Exception as e:
            print(f"\nAn unexpected error occurred: {e}")


# --- Main Execution ---

if __name__ == "__main__":
    controller = AppController()
    controller.run()
