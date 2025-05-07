import sys


op_codes = {
    "000000": "R",  # shared for craft, mine, etc.
    "000010": "flint",
    "000011": "steel",
    "000100": "enderman",
    "000101": "TheNether",
    "000110": "CraftingTable",
    "111000": "RedStone",
    "111001": "BedWars",
    "111010": "Steve",
    "111011": "HappyGhast"
}

func_codes = {
    "100000": "craft",
    "100010": "mine",
    "011010": "elytra",
    "010000": "DiamondPickAxe",
    "101001": "BedWars"
}

registers = {
    "00000": "$zero",
    "01001": "$t1",
    "01010": "$t2",
    "01011": "$t3",
    "01100": "$t4",
    "01101": "$t5",
    "01110": "$t6",
    "01111": "$t7",
    "10000": "$s0",
    "10001": "$s1",
    "10010": "$s2",
    "10011": "$s3",
    "10100": "$s4",
    "10101": "$s5",
    "10110": "$s6",
    "10111": "$s7",
}


def handle_lines(bin_file: str):
    with open(bin_file, "r", encoding="utf-8") as input_file:
        lines = [line.strip() for line in input_file.readlines() if line.strip()]

    if not lines:
        print("⚠️ program1.bin is empty!")
        return

    print(f"✅ Read {len(lines)} valid lines from {bin_file}")

    all_mips = []

    for line in lines:
        instructions = bin_to_mips(line)
        all_mips.extend(instructions)

    if not all_mips:
        print("⚠️ No instructions were decoded!")
        return

    with open("BACK_TO_MIPS.txt", "w", encoding="utf-8") as output_file:
        for instruction in all_mips:
            print(instruction)  # TEMP: See output
            output_file.write(instruction + "\n")



def bin_to_mips(line):
    mips = []
    bit_string = ""

    for i in range(len(line)):
        bit_string += line[i]
        if len(bit_string) == 32:
            op_code = bit_string[0:6]

            if op_code == "000000":  # R-type
                rs = bit_string[6:11]
                rt = bit_string[11:16]
                rd = bit_string[16:21]
                shift = bit_string[21:26]
                func_code = bit_string[26:32]
                instr = func_codes.get(func_code, "UNKNOWN")
                mips.append(f"{instr} {registers[rd]}, {registers[rs]}, {registers[rt]}")

            elif op_code == "111011":  # HappyGhast
                rt = bit_string[11:16]
                mips.append(f"HappyGhast {registers[rt]}")

            elif op_code == "111010":  # Steve
                mips.append("Steve")

            elif op_code == "111000":  # RedStone
                mips.append("RedStone")

            elif op_code == "000110":  # CraftingTable (J-type)
                address = int(bit_string[6:], 2)
                mips.append(f"CraftingTable {address}")

            else:  # I-type fallback
                rs = bit_string[6:11]
                rt = bit_string[11:16]
                imm = bit_string[16:32]
                instr = op_codes.get(op_code, "UNKNOWN")
                mips.append(f"{instr} {registers[rt]}, {registers[rs]}, {int(imm, 2)}")

            bit_string = ""

    return mips



if __name__ == "__main__":
    handle_lines("program1.bin")
