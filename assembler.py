import sys
import os


op_codes = {
    "craft": "000000",     # add
    "mine": "000000",      # sub
    "elytra": "000000",    # div
    "flint": "000010",     # addi
    "steel": "000011",     # beq
    "enderman": "000100",  # li
    "TheNether": "000101", # la
    "DiamondPickAxe": "000000", # mfhi
    "CraftingTable": "000110", # j
    "RedStone": "111000",  # newline / syscall
    "BedWars": "111001",
    "Steve": "111010",
    "HappyGhast": "111011"
}

func_codes = {
    "craft": "100000",
    "mine": "100010",
    "elytra": "011010",     # MIPS-style div
    "DiamondPickAxe": "010000",  # MIPS mfhi
    "BedWars": "101001"
}

registers = {
    "$zero": "00000",
    "$t1": "01001",
    "$t2": "01010",
    "$t3": "01011",
    "$t4": "01100",
    "$t5": "01101",
    "$t6": "01110",
    "$t7": "01111",
    "$s0": "10000",
    "$s1": "10001",
    "$s2": "10010",
    "$s3": "10011",
    "$s4": "10100",
    "$s5": "10101",
    "$s6": "10110",
    "$s7": "10111",
}
shift_logic_amount = "00000"


def interpret_line(mips_file: str):
    input_file = open(mips_file, "r", encoding="utf-8")
    output_file = open("program1.bin", "w")
    for instruction in input_file:
        bin = assemble(instruction)
        output_file.write(bin + "\n")


def assemble(line):
    line = line.split("#")[0].strip()
    if not line:
        return ""

    parts = [p.strip(",") for p in line.split()]

    op_code = parts[0]

    # Handle R-type instructions with funct codes
    if op_code in ["craft", "mine", "elytra", "DiamondPickAxe", "BedWars"]:
        if op_code == "DiamondPickAxe":
            rd = parts[1]
            return (
                op_codes[op_code]
                + "00000"  # rs
                + "00000"  # rt
                + registers[rd]
                + shift_logic_amount
                + func_codes[op_code]
            )
        elif op_code == "BedWars":
            rd, rs = parts[1].replace(",", ""), parts[2]
            return (
                op_codes[op_code]
                + registers[rs]
                + "00000"
                + registers[rd]
                + shift_logic_amount
                + func_codes[op_code]
            )
        else:
            rd, rs, rt = (
                parts[1].replace(",", ""),
                parts[2].replace(",", ""),
                parts[3].replace(",", ""),
            )
            return (
                op_codes[op_code]
                + registers[rs]
                + registers[rt]
                + registers[rd]
                + shift_logic_amount
                + func_codes[op_code]
            )

    # I-type instructions
    elif op_code in ["flint", "steel", "enderman", "TheNether"]:
        rt, rs, imm = (
            parts[1].replace(",", ""),
            parts[2].replace(",", ""),
            parts[3]
        )
        imm_bin = bin(int(imm)).replace("0b", "").zfill(16)
        return op_codes[op_code] + registers[rs] + registers[rt] + imm_bin

    # J-type instruction
    elif op_code == "CraftingTable":
        address = int(parts[1], 0)
        address_bin = bin(address).replace("0b", "").zfill(26)
        return op_codes[op_code] + address_bin

    # S-type (no operand) instructions like Steve, RedStone, HappyGhast
    elif op_code in ["Steve", "RedStone"]:
        return op_codes[op_code] + "0" * 26

    elif op_code == "HappyGhast":
        rt = parts[1]
        return op_codes[op_code] + "00000" + registers[rt] + "0" * 16

    else:
        print(f"Unknown instruction: {op_code}")
        return ""


if __name__ == "__main__":
    # mips_file = sys.argv[1]
    mips_file = "program1.mips"
    interpret_line(mips_file)
