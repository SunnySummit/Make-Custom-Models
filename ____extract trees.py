import os
import sys
import re
import xml.etree.ElementTree as ET
from hgpaktool import HGPakFile, Compressor, Platform

# initialize compressor
compressor = Compressor(Platform.WINDOWS) # for windows

# VARIABLES

pak_path = "" ## yours here, e.g. _____/steamapps/common/No Man's Sky/GAMEDATA/PCBANKS
output_dir = "CUSTOMMODELS"

prism_output_dir = f"{output_dir}/TREES_PRISM"
noleaves_output_dir = f"{output_dir}/TREES_NOLEAVES"

extract_trees_prism_pine = ["MODELS/PLANETS/BIOMES/HQLUSH/HQTREES/"]
extract_trees_no_leaves = ["MODELS/PLANETS/BIOMES/HQLUSH/HQTREES/"]
mxml_files = []

# REPLACE BLOCKS

# create new blocks via parsing XML fragments (strip for valid start)

########################## pine twig

samplers_block_pine_twig = """
<Property name="Samplers">
	<Property name="Samplers" value="TkMaterialSampler" _index="0">
		<Property name="Name" value="gDiffuseMap" />
		<Property name="Map" value="TEXTURES/PLANETS/BIOMES/CAVE/MEDIUMPROP/MEDIUMGLOWPLANT.BASE.DDS" />
		<Property name="IsCube" value="false" />
		<Property name="UseCompression" value="true" />
		<Property name="UseMipMaps" value="true" />
		<Property name="IsSRGB" value="true" />
		<Property name="MaterialAlternativeId" value="" />
		<Property name="TextureAddressMode" value="Wrap" />
		<Property name="TextureFilterMode" value="Trilinear" />
		<Property name="Anisotropy" value="0" />
	</Property>
	<Property name="Samplers" value="TkMaterialSampler" _index="1">
		<Property name="Name" value="gNormalMap" />
		<Property name="Map" value="TEXTURES/PLANETS/BIOMES/CAVE/MEDIUMPROP/MEDIUMGLOWPLANT.BASE.NORMAL.DDS" />
		<Property name="IsCube" value="false" />
		<Property name="UseCompression" value="true" />
		<Property name="UseMipMaps" value="true" />
		<Property name="IsSRGB" value="false" />
		<Property name="MaterialAlternativeId" value="" />
		<Property name="TextureAddressMode" value="Wrap" />
		<Property name="TextureFilterMode" value="Trilinear" />
		<Property name="Anisotropy" value="0" />
	</Property>
</Property>
""".strip()

flags_block_pine_twig = """
<Property name="Flags">
	<Property name="Flags" value="TkMaterialFlags" _index="0">
		<Property name="MaterialFlag" value="_F01_DIFFUSEMAP" />
	</Property>
	<Property name="Flags" value="TkMaterialFlags" _index="1">
		<Property name="MaterialFlag" value="_F03_NORMALMAP" />
	</Property>
	<Property name="Flags" value="TkMaterialFlags" _index="2">
		<Property name="MaterialFlag" value="_F36_DOUBLESIDED" />
	</Property>
</Property>
""".strip()

########################## prism leaves

samplers_block_prism = """
<Property name="Samplers">
	<Property name="Samplers" value="TkMaterialSampler" _index="0">
		<Property name="Name" value="gDiffuseMap" />
		<Property name="Map" value="TEXTURES/PLANETS/BIOMES/FLORAL/MEDIUMCREATURE/PROCGLOWGRADIENT.BASE.DDS" />
		<Property name="IsCube" value="false" />
		<Property name="UseCompression" value="true" />
		<Property name="UseMipMaps" value="true" />
		<Property name="IsSRGB" value="true" />
		<Property name="MaterialAlternativeId" value="" />
		<Property name="TextureAddressMode" value="Wrap" />
		<Property name="TextureFilterMode" value="Trilinear" />
		<Property name="Anisotropy" value="0" />
	</Property>
	<Property name="Samplers" value="TkMaterialSampler" _index="1">
		<Property name="Name" value="gMasksMap" />
		<Property name="Map" value="TEXTURES/PLANETS/BIOMES/FLORAL/MEDIUMCREATURE/PROCGLOWGRADIENT.BASE.MASKS.DDS" />
		<Property name="IsCube" value="false" />
		<Property name="UseCompression" value="true" />
		<Property name="UseMipMaps" value="true" />
		<Property name="IsSRGB" value="false" />
		<Property name="MaterialAlternativeId" value="" />
		<Property name="TextureAddressMode" value="Wrap" />
		<Property name="TextureFilterMode" value="Trilinear" />
		<Property name="Anisotropy" value="0" />
	</Property>
</Property>
""".strip()

flags_block_prism = """
<Property name="Flags">
	<Property name="Flags" value="TkMaterialFlags" _index="0">
		<Property name="MaterialFlag" value="_F01_DIFFUSEMAP" />
	</Property>
	<Property name="Flags" value="TkMaterialFlags" _index="1">
		<Property name="MaterialFlag" value="_F15_WIND" />
	</Property>
	<Property name="Flags" value="TkMaterialFlags" _index="2">
		<Property name="MaterialFlag" value="_F21_VERTEXCUSTOM" />
	</Property>
	<Property name="Flags" value="TkMaterialFlags" _index="3">
		<Property name="MaterialFlag" value="_F25_MASKS_MAP" />
	</Property>
	<Property name="Flags" value="TkMaterialFlags" _index="4">
		<Property name="MaterialFlag" value="_F36_DOUBLESIDED" />
	</Property>
</Property>
""".strip() # end else

########################## no leaves

samplers_block_no_leaves = """
<Property name="Samplers" />
""".strip()

flags_block_no_leaves = """
<Property name="Flags" />
""".strip() # end else


# FUNCTIONS

# helper to parse and replace blocks
def replace_material_file(filepath, relative_path, nw_samplers_block, nw_flags_block, vrfy_pines_etc):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    countent_lower = content.lower()

    if vrfy_pines_etc: # if need to verify if pines in the file
        
        # [a] check for CROSSLEAF <- these cause issues
        if "crossleaf" in countent_lower:
            return False
        
        # [b] for pine trees = unique samplers and flags
        elif "twigbranch" in countent_lower or "pine" in countent_lower:

            new_samplers_block = samplers_block_pine_twig
            new_flags_block = flags_block_pine_twig

        # [c] everything else - prism trees
        else:
            new_samplers_block = nw_samplers_block
            new_flags_block = nw_flags_block

    else:
        new_samplers_block = nw_samplers_block
        new_flags_block = nw_flags_block


    # capture xml declaration and first comment (if present) so we can reinsert them
    xml_decl = ""
    leading_comment = ""
    rest = content.lstrip()
    prefix_len = len(content) - len(rest)
    prefix = content[:prefix_len]

    if rest.startswith('<?xml'):
        end_decl = rest.find('?>')
        if end_decl != -1:
            xml_decl = rest[:end_decl+2].strip() + "\n"
            rest = rest[end_decl+2:].lstrip()

    if rest.startswith('<!--'):
        end_comment = rest.find('-->')
        if end_comment != -1:
            leading_comment = rest[:end_comment+3].strip() + "\n"
            rest = rest[end_comment+3:].lstrip()

    # now rest should start with <Data ...>
    try:
        root = ET.fromstring(rest)
    except ET.ParseError as e:
        print(f"Failed to parse XML for {relative_path}: {e}")
        return False

    # parse fragments into Elements
    new_samplers_elem = ET.fromstring(new_samplers_block)
    new_flags_elem = ET.fromstring(new_flags_block)

    # find top-level child indices for insertion/replacement
    # root is the <Data> element. iterate its direct children to keep order
    children = list(root)  # snapshot
    replaced_any = False

    # replace top-level Samplers block if present
    for i, child in enumerate(children):
        if child.tag == "Property" and child.attrib.get("name", "").lower() == "samplers":
            root.remove(child)
            root.insert(i, new_samplers_elem)
            replaced_any = True
            break

    # replace top-level Flags block if present
    # re-evaluate children list because we may have modified it
    children = list(root)
    for i, child in enumerate(children):
        if child.tag == "Property" and child.attrib.get("name", "").lower() == "flags":
            root.remove(child)
            root.insert(i, new_flags_elem)
            replaced_any = True
            break

    # set individual properties anywhere in the tree
    replacements = {
        "MaterialClass": "DoubleSided",
        "CastShadow": "true",
        "EnableLodFade": "true",
        "UseShaderMill": "false",
        "Shader": "SHADERS/UBERSHADER.SHADER.BIN",
    }

    for prop_name, new_value in replacements.items():
        for elem in root.iter("Property"):
            if elem.attrib.get("name", "") == prop_name:
                elem.set("value", new_value) # set or replace the 'value' attribute (works for single-line properties)
                replaced_any = True

    if not replaced_any:
        # nothing changed. still ok, but return False to indicate no change if needed
        pass

    # format tree with consistent tab indentation
    ET.indent(root, space="\t", level=0)

    # serialize without pretty-printing (prevents empty lines)
    xml_body = ET.tostring(root, encoding="unicode")

    # rebuild output
    if xml_decl:
        out = xml_decl
    else:
        out = '<?xml version="1.0" encoding="utf-8"?>\n'

    if leading_comment:
        out += leading_comment

    out += xml_body + "\n"

    with open(filepath, "w", encoding="utf-8", newline="\n") as f:
        f.write(out)

    return True


# helper to extract and edit files
def extract_edit_files(cm_subfolder, new_samplers_block, new_flags_block, check_pines_etc):

    mxml_files = [] # reset list

    # verify files decompiled
    for root, dirs, files in os.walk(cm_subfolder):
        for file in files:
            name = file.lower()
            path = os.path.join(root, file)

            if name.endswith(".mxml"):
                mxml_files.append(path)

    #if none found, exit
    if not mxml_files:
        print(f"\n\nError. No MXML files found within '{cm_subfolder}'. Exiting...")
        sys.exit(0)

    print(f"\nModifying subfolder: {cm_subfolder}\n")

    for filepath in mxml_files:
        filename_lower = os.path.basename(filepath).lower()

        normalized = os.path.normpath(filepath)  # use actual filepath for relative extraction
        parts = normalized.replace("\\", "/").split("/")
        if "models" in [p.lower() for p in parts]:
            index = [p.lower() for p in parts].index("models")
            relative_path = "/".join(parts[index:])
        else:
            relative_path = os.path.basename(filepath)

        if (filename_lower.endswith("material.mxml")
            and "bark" not in filename_lower
            and "lambert" not in filename_lower):

            ok = replace_material_file(filepath, relative_path, new_samplers_block, new_flags_block, check_pines_etc)
            if ok:
                print(f"+Modified material: {relative_path}")
            else:
                print(f"-No changes made for: {relative_path}")

        # process the other non-materials files, etc
        else:

            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            # regex pattern:
            # matches:
            #MODELS\PLANETS\BIOMES\HQLUSH\HQTREES\....SCENE.MBIN
            #MODELS\PLANETS\BIOMES\HQLUSH\HQTREES\....MATERIAL.MBIN
            #But not ....GEOMETRY.MBIN etc.

            pattern = re.compile(
                r'(?:CUSTOMMODELS[\\/][^"\r\n]*?[\\/])?'
                r'(MODELS[\\/]PLANETS[\\/]BIOMES[\\/]HQLUSH[\\/]HQTREES[\\/][^"\r\n]*?'
                r'(?:SCENE|MATERIAL)\.MBIN)'
            )

            new_content = pattern.sub(rf'{cm_subfolder}\\\1', content)

            
            #pattern = re.compile(
            #    r'(?<!CUSTOMMODELS[\\/])'  # prevent double prefix (both separators)
            #    r'(MODELS[\\/]PLANETS[\\/]BIOMES[\\/]HQLUSH[\\/]HQTREES[\\/][^"\r\n]*?'
            #    r'(?:SCENE|MATERIAL)\.MBIN)'
            #)

            #new_content = pattern.sub(r'CUSTOMMODELS\\\1', content)
            

            if new_content != content:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(new_content)

                print(f"!Modified scene/descriptor: {relative_path}")






# process .pak files in PCBANKS
for filename in os.listdir(pak_path):
    
    if ".pak" in filename.lower():
    
        pak_file = os.path.join(pak_path, filename)
        
        with open(pak_file, "rb") as pak:

            hgpak = HGPakFile(pak, compressor)
            hgpak.read()

            hgpak.unpack(prism_output_dir, directories=extract_trees_prism_pine)
            hgpak.unpack(noleaves_output_dir, directories=extract_trees_no_leaves)

# remove geometry files before decompiling
for root, dirs, files in os.walk(output_dir):
    for file in files:
        name = file.lower()
        path = os.path.join(root, file)

        if "geometry" in name: # remove any geometry files
            os.remove(path)
            continue

input("\nExtracted vanilla MBINs. Drag and drop 'custommodels' folder to latest MBINCompiler.exe. Press Enter to continue...")

# extract and edit each subfolder with unique data
extract_edit_files(prism_output_dir, samplers_block_prism, flags_block_prism, check_pines_etc = True)
extract_edit_files(noleaves_output_dir, samplers_block_no_leaves, flags_block_no_leaves, check_pines_etc = True)





#call here


input("\nDouble-check all modified MXMLs, drag and drop 'custommodels' folder to MBINCompiler to recompile back to MBIN." \
"\nMove 'custommodels' to '+BPG Redux Planets Core' directory."
"\n\nPress Enter to exit...")