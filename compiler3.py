import re
import sys
import os


class Compiler:
    def __init__(self):
        self.reset_compiler()

    #Set the data and memory address
    def reset_compiler(self):
        self.memory_address = 5000
        self.t_register = 0
        self.vars = {}
        self.labels = 0
        self.string_data = {}
        self.data_section = []
        self.text_section = []
        self.current_while_stack = []

    def get_temp_reg(self):
        reg = f"$t{self.t_register}"
        self.t_register += 1
        if self.t_register > 7:  # Reset to avoid running out of t registers (t0-t7)
            self.t_register = 0
        return reg

    def declare_variable(self, var_name):
        if var_name not in self.vars:
            self.vars[var_name] = {'addr': self.memory_address}
            self.memory_address += 4
            # Add comment for variable declaration
            # self.text_section.append(f"# Declare variable {var_name} at address {self.vars[var_name]['addr']}")

    def get_var_addr(self, var_name):
        if var_name in self.vars:
            return self.vars[var_name]['addr']
        return None

    def new_label(self):
        self.labels += 1
        return f"L{self.labels}"

    def process_escape_sequences(self, string):
        """Process escape sequences for MIPS string storage."""
        # Handle \n specially for MIPS
        processed = string.replace('\\n', '\\n')
        return processed

    def add_string(self, value):
        """Store a string in the data section and return its label."""

        if value not in self.string_data:
            label = f"str_{len(self.string_data)}"
            self.string_data[value] = label

            # Properly process escape sequences for MIPS
            # Keep the string as is - MIPS assembler will handle standard escape sequences
            # Just ensure proper formatting for the .asciiz directive

            self.data_section.append(f'{label}: .asciiz "{value}"')

        return self.string_data[value]

    def extract_minecraft_instructions(self, c_code):
        """Extract Minecraft-themed instructions from C code."""
        # Check for special case first
        if c_code.lstrip().startswith("IronGolem $t0"):
            return "IronGolem $t0"

        # Define regex pattern to match all Minecraft instructions
        pattern = r'(Steve|EnderDragon|LavaChicken|GoldenApple|Creeper|BedWars\s+\$t\d+\s*,\s*\$\w+|ChickenJockey\s+\$t\d+\s*,\s*\$t\d+|CrushinLoaf\s+\$t\d+|IronGolem\s+\$t\d+|HappyGhast\s+\$t\d+)\s*;'

        # Find all matches in the code
        matches = re.finditer(pattern, c_code)

        # Extract each match without the trailing semicolon
        instructions = []
        for match in matches:
            instruction = match.group(1).strip()
            instructions.append(instruction)

        # Return the extracted instructions as a string
        return "\n".join(instructions)

    def add_minecraft_instruction(self, instruction):
        """Add a minecraft instruction to the tracking list."""
        self.minecraft_instructions.append(instruction)
        # Also add a placeholder comment in the standard MIPS assembly
        self.text_section.append(f"# Minecraft Instruction: {instruction}")

    def compile_statement(self, statement):
        statement = statement.strip()

        # Handle empty statements
        if not statement:
            return

        # Handle Minecraft custom instructions
        if statement.startswith('Steve;'):
            self.add_minecraft_instruction("Steve")
        elif statement.startswith('EnderDragon;'):
            self.add_minecraft_instruction("EnderDragon")
        elif statement.startswith('LavaChicken;'):
            self.add_minecraft_instruction("LavaChicken")
        elif statement.startswith('GoldenApple;'):
            self.add_minecraft_instruction("GoldenApple")
        elif statement.startswith('Creeper;'):
            self.add_minecraft_instruction("Creeper")
        elif statement.startswith('BedWars '):
            args = statement[7:].split(';')[0].strip()
            self.add_minecraft_instruction(f"BedWars {args}")
        elif statement.startswith('ChickenJockey '):
            args = statement[13:].split(';')[0].strip()
            self.add_minecraft_instruction(f"ChickenJockey {args}")
        elif statement.startswith('CrushinLoaf '):
            args = statement[12:].split(';')[0].strip()
            self.add_minecraft_instruction(f"CrushinLoaf {args}")
        elif statement.startswith('IronGolem '):
            args = statement[10:].split(';')[0].strip()
            self.add_minecraft_instruction(f"IronGolem {args}")
        elif statement.startswith('HappyGhast '):
            args = statement[11:].split(';')[0].strip()
            self.add_minecraft_instruction(f"HappyGhast {args}")
        # Variable declaration
        elif statement.startswith('int '):
            var_name = statement[4:].split(';')[0].strip()
            self.declare_variable(var_name)
        # Assignment
        elif '=' in statement and not statement.startswith('if') and not statement.startswith('while'):
            parts = statement.split('=', 1)
            target = parts[0].strip()
            value = parts[1].split(';')[0].strip()
            self.compile_assignment(target, value)
        # While loop
        elif statement.startswith('while ('):
            condition = re.search(r'while\s*\((.*?)\)', statement).group(1).strip()
            body_start = statement.find('{') + 1
            body_end = self.find_matching_brace(statement, body_start - 1)
            body = statement[body_start:body_end].strip()
            self.compile_while(condition, body)
        # If statement
        elif statement.startswith('if ('):
            condition = re.search(r'if\s*\((.*?)\)', statement).group(1).strip()
            body_start = statement.find('{') + 1
            body_end = self.find_matching_brace(statement, body_start - 1)
            body = statement[body_start:body_end].strip()
            self.compile_if(condition, body)
        # Print string statement
        elif 'print_str' in statement:
            try:
                match = re.search(r'print_str\s*\(\s*"(.*?)"\s*\)', statement, re.DOTALL)
                if match:
                    value = match.group(1)
                else:
                    value = self.extract_string_from_print(statement)
                self.compile_print('str', value)
            except Exception as e:
                print(f"Error extracting string: {e}\nStatement: {statement}")
        # Print int statement
        elif 'print_int' in statement:
            try:
                value = re.search(r'print_int\s*\(\s*(.*?)\s*\)', statement).group(1).strip()
                self.compile_print('int', value)
            except Exception as e:
                print(f"Error extracting int: {e}\nStatement: {statement}")
        # Multiple statements (separated by semicolons)
        elif ';' in statement and not re.search(r'".*;.*"', statement):  # Avoid splitting inside string literals
            statements = self.split_statements_by_semicolon(statement)
            for stmt in statements:
                if stmt.strip():
                    self.compile_statement(stmt.strip() + ';')

    def compile_assignment(self, target, value):
        # Add comment
        self.text_section.append(f"# {target} = {value}")

        # Handle constant assignments
        if value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
            reg = self.get_temp_reg()
            self.text_section.append(f"enderman {reg}, {value}")
            self.text_section.append(f"pickaxe {reg}, {self.get_var_addr(target)}")
        # Handle variable assignments
        elif value in self.vars:
            reg1 = self.get_temp_reg()
            self.text_section.append(f"elytra {reg1}, {self.get_var_addr(value)}")
            self.text_section.append(f"pickaxe {reg1}, {self.get_var_addr(target)}")
        # Handle arithmetic operations
        elif any(op in value for op in ['+', '-', '*', '/', '%']):
            self.compile_arithmetic(target, value)

    def compile_arithmetic(self, target, expr):
        # Handle modulus operation
        if '%' in expr:
            var1, var2 = expr.split('%')
            var1 = var1.strip()
            var2 = var2.strip()

            self.text_section.append(f"# Compute {var1} % {var2}")
            reg1 = self.get_temp_reg()
            reg2 = self.get_temp_reg()
            result = self.get_temp_reg()

            # Load first operand
            if var1.isdigit() or (var1.startswith('-') and var1[1:].isdigit()):
                self.text_section.append(f"endermen {reg1}, {var1}")
            else:
                self.text_section.append(f"elytra {reg1}, {self.get_var_addr(var1)}")

            # Load second operand
            if var2.isdigit() or (var2.startswith('-') and var2[1:].isdigit()):
                self.text_section.append(f"endermen {reg2}, {var2}")
            else:
                self.text_section.append(f"elytra {reg2}, {self.get_var_addr(var2)}")

            #put all of the operands together
            self.text_section.append(f"div {reg1}, {reg2}")
            self.text_section.append(f"diamondpickaxe {result}")  # Get remainder
            self.text_section.append(f"pickaxe {result}, {self.get_var_addr(target)}")

        # Handle addition
        elif '+' in expr:
            var1, var2 = expr.split('+')
            var1 = var1.strip()
            var2 = var2.strip()

            self.text_section.append(f"# Compute {var1} + {var2}")
            reg1 = self.get_temp_reg()
            reg2 = self.get_temp_reg()
            result = self.get_temp_reg()

            # Load first operand
            if var1.isdigit() or (var1.startswith('-') and var1[1:].isdigit()):
                self.text_section.append(f"enderman {reg1}, {var1}")
            else:
                self.text_section.append(f"elytra {reg1}, {self.get_var_addr(var1)}")

            # Load second operand
            if var2.isdigit() or (var2.startswith('-') and var2[1:].isdigit()):
                self.text_section.append(f"endermen {reg2}, {var2}")
            else:
                self.text_section.append(f"elytra {reg2}, {self.get_var_addr(var2)}")

            self.text_section.append(f"craft {result}, {reg1}, {reg2}")
            self.text_section.append(f"pickaxe {result}, {self.get_var_addr(target)}")

    def compile_if(self, condition, body):
        end_label = self.new_label()

        # Print the original condition and body for debugging
        # print(f"Compiling if condition: '{condition}' with body: '{body}'")

        # Handle equality condition
        if '==' in condition:
            var1, var2 = condition.split('==')
            var1 = var1.strip()
            var2 = var2.strip()

            self.text_section.append(f"# if ({var1} == {var2})")
            reg1 = self.get_temp_reg()
            reg2 = self.get_temp_reg()

            # Load first operand
            if var1.isdigit() or (var1.startswith('-') and var1[1:].isdigit()):
                self.text_section.append(f"endermen {reg1}, {var1}")
            else:
                self.text_section.append(f"elytra {reg1}, {self.get_var_addr(var1)}")

            # Load second operand
            if var2.isdigit() or (var2.startswith('-') and var2[1:].isdigit()):
                self.text_section.append(f"endermen {reg2}, {var2}")
            else:
                self.text_section.append(f"elytra {reg2}, {self.get_var_addr(var2)}")

            # Branch if not equal (skip the if body)
            self.text_section.append(f"emerald {reg1}, {reg2}, {end_label}")

        # Handle logical AND
        elif '&&' in condition:
            parts = condition.split('&&')
            left = parts[0].strip()
            right = parts[1].strip()

            self.text_section.append(f"# if ({left} && {right})")

            # We need to check both conditions, if either fails, skip the body
            left_var, left_val = left.split('==')
            right_var, right_val = right.split('==')

            left_var = left_var.strip()
            left_val = left_val.strip()
            right_var = right_var.strip()
            right_val = right_val.strip()

            reg1 = self.get_temp_reg()
            reg2 = self.get_temp_reg()
            reg3 = self.get_temp_reg()
            reg4 = self.get_temp_reg()

            # First condition
            if left_var.isdigit() or (left_var.startswith('-') and left_var[1:].isdigit()):
                self.text_section.append(f"enderman {reg1}, {left_var}")
            else:
                self.text_section.append(f"elytra {reg1}, {self.get_var_addr(left_var)}")

            if left_val.isdigit() or (left_val.startswith('-') and left_val[1:].isdigit()):
                self.text_section.append(f"endermen {reg2}, {left_val}")
            else:
                self.text_section.append(f"elytra {reg2}, {self.get_var_addr(left_val)}")

            # If first condition fails, skip
            self.text_section.append(f"emerald {reg1}, {reg2}, {end_label}")

            # Second condition
            if right_var.isdigit() or (right_var.startswith('-') and right_var[1:].isdigit()):
                self.text_section.append(f"endermen {reg3}, {right_var}")
            else:
                self.text_section.append(f"elytra {reg3}, {self.get_var_addr(right_var)}")

            if right_val.isdigit() or (right_val.startswith('-') and right_val[1:].isdigit()):
                self.text_section.append(f"endermen {reg4}, {right_val}")
            else:
                self.text_section.append(f"elytra {reg4}, {self.get_var_addr(right_val)}")

            # If second condition fails, skip
            self.text_section.append(f"emerald {reg3}, {reg4}, {end_label}")

        # Compile the if body
        body_statements = self.split_compound_statement(body)
        # print(f"If body split into {len(body_statements)} statements: {body_statements}")

        for stmt in body_statements:
            self.compile_statement(stmt)

        self.text_section.append(f"{end_label}:")

    def compile_while(self, condition, body):
        start_label = self.new_label()
        end_label = self.new_label()

        self.text_section.append(f"# while ({condition})")
        self.text_section.append(f"{start_label}:")

        # Handle less than condition
        if '<' in condition:
            var1, var2 = condition.split('<')
            var1 = var1.strip()
            var2 = var2.strip()

            reg1 = self.get_temp_reg()
            reg2 = self.get_temp_reg()

            # Load first operand
            if var1.isdigit() or (var1.startswith('-') and var1[1:].isdigit()):
                self.text_section.append(f"enderman {reg1}, {var1}")
            else:
                self.text_section.append(f"elytra {reg1}, {self.get_var_addr(var1)}")

            # Load second operand
            if var2.isdigit() or (var2.startswith('-') and var2[1:].isdigit()):
                self.text_section.append(f"enderman {reg2}, {var2}")
            else:
                self.text_section.append(f"elytra {reg2}, {self.get_var_addr(var2)}")

            # Branch if greater or equal (opposite of less than)
            self.text_section.append(f"steel {reg1}, {reg2}, {end_label}")

        # Compile body - splitting compound statements
        for stmt in self.split_compound_statement(body):
            self.compile_statement(stmt)

        # Jump back to start
        self.text_section.append(f"craftingTable {start_label}")
        self.text_section.append(f"{end_label}:")

    def extract_string_from_print(self, statement):
        """Extract the string from a print_str statement, handling escaped quotes."""
        # Find the opening parenthesis and opening quote
        start_paren = statement.find('(')
        start_quote = statement.find('"', start_paren)

        if start_paren == -1 or start_quote == -1:
            print(f"Warning: Could not find opening parenthesis or quote in: {statement}")
            return ""

        # Find the closing quote, accounting for escaped quotes
        pos = start_quote + 1
        while pos < len(statement):
            if statement[pos] == '"' and statement[pos - 1] != '\\':
                break
            pos += 1

        if pos >= len(statement):
            print(f"Warning: No closing quote found in: {statement}")
            return ""  # No closing quote found

        # Extract the string content
        return statement[start_quote + 1:pos]

    def compile_print(self, print_type, value):
        if print_type == 'str':
            self.text_section.append(f"# print_str(\"{value}\")")
            label = self.add_string(value)
            # Check if the string was added successfully
            if label:
                self.text_section.append(f"endermen $v0, 4")
                self.text_section.append(f"TheNether $a0, {label}")
                self.text_section.append(f"syscall")
            else:
                print(f"Warning: Failed to add string: '{value}'")
        elif print_type == 'int':
            self.text_section.append(f"# print_int({value})")
            reg = self.get_temp_reg()

            if value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
                self.text_section.append(f"endermen {reg}, {value}")
            else:
                addr = self.get_var_addr(value)
                if addr is not None:
                    self.text_section.append(f"elytra {reg}, {addr}")
                else:
                    print(f"Warning: Variable '{value}' not declared")
                    return

            self.text_section.append(f"Teleport $a0, {reg}")
            self.text_section.append(f"endermen $v0, 1")
            self.text_section.append(f"Bedrock")

    def compile_statement(self, statement):
        statement = statement.strip()

        # print(f"Compiling statement: '{statement}'")

        # Handle empty statements
        if not statement:
            return

        # Variable declaration
        if statement.startswith('int '):
            var_name = statement[4:].split(';')[0].strip()
            self.declare_variable(var_name)

        # Assignment
        elif '=' in statement and not statement.startswith('if') and not statement.startswith('while'):
            parts = statement.split('=', 1)
            target = parts[0].strip()
            value = parts[1].split(';')[0].strip()
            self.compile_assignment(target, value)

        # While loop
        elif statement.startswith('while ('):
            condition = re.search(r'while\s*\((.*?)\)', statement).group(1).strip()
            body_start = statement.find('{') + 1
            body_end = self.find_matching_brace(statement, body_start - 1)
            body = statement[body_start:body_end].strip()
            self.compile_while(condition, body)

        # If statement
        elif statement.startswith('if ('):
            condition = re.search(r'if\s*\((.*?)\)', statement).group(1).strip()
            body_start = statement.find('{') + 1
            body_end = self.find_matching_brace(statement, body_start - 1)
            body = statement[body_start:body_end].strip()
            self.compile_if(condition, body)

        # Print string statement
        elif 'print_str' in statement:
            # Use the improved string extraction method
            try:
                # First try standard regex but it might fail with complex strings
                match = re.search(r'print_str\s*\(\s*"(.*?)"\s*\)', statement, re.DOTALL)
                if match:
                    value = match.group(1)
                else:
                    # Fallback to manual extraction
                    value = self.extract_string_from_print(statement)
                # print(f"Extracted string: '{value}'")
                self.compile_print('str', value)
            except Exception as e:
                print(f"Error extracting string: {e}\nStatement: {statement}")

        # Print int statement
        elif 'print_int' in statement:
            try:
                value = re.search(r'print_int\s*\(\s*(.*?)\s*\)', statement).group(1).strip()
                self.compile_print('int', value)
            except Exception as e:
                print(f"Error extracting int: {e}\nStatement: {statement}")

        # Multiple statements (separated by semicolons)
        elif ';' in statement and not re.search(r'".*;.*"', statement):  # Avoid splitting inside string literals
            statements = self.split_statements_by_semicolon(statement)
            for stmt in statements:
                if stmt.strip():
                    self.compile_statement(stmt.strip() + ';')

    def split_statements_by_semicolon(self, text):
        """Split by semicolons outside of string literals"""
        result = []
        current = ""
        in_string = False

        for char in text:
            if char == '"' and not in_string:
                in_string = True
                current += char
            elif char == '"' and in_string:
                in_string = False
                current += char
            elif char == ';' and not in_string:
                result.append(current)
                current = ""
            else:
                current += char

        if current:
            result.append(current)
        return result

    def find_matching_brace(self, text, open_pos):
        depth = 1
        for i in range(open_pos + 1, len(text)):
            if text[i] == '{':
                depth += 1
            elif text[i] == '}':
                depth -= 1
                if depth == 0:
                    return i
        return len(text)  # If no matching brace is found

    def split_statements(self, code):
        # Split code into individual statements
        statements = []
        current = ""
        brace_level = 0
        in_string = False

        i = 0
        while i < len(code):
            char = code[i]

            # Handle strings with proper escaped quote handling
            if char == '"' and (i == 0 or code[i - 1] != '\\'):
                in_string = not in_string

            # Only count braces outside of strings
            if not in_string:
                if char == '{':
                    brace_level += 1
                elif char == '}':
                    brace_level -= 1

            current += char

            # End of statement if semicolon or closing brace at top level
            if not in_string and brace_level == 0 and (char == ';' or char == '}'):
                statements.append(current.strip())
                current = ""

            i += 1

        # Add the last statement if it exists
        if current.strip():
            statements.append(current.strip())

        return statements

    def split_compound_statement(self, body):
        """Split a compound statement (code block) into individual statements"""
        result = []
        current = ""
        in_string = False
        brace_level = 0

        # Debug
        # print(f"Splitting compound statement: {body}")

        i = 0
        while i < len(body):
            char = body[i]

            # Track string literals with proper escaped quote handling
            if char == '"' and (i == 0 or body[i - 1] != '\\'):
                in_string = not in_string

            # Track nested braces
            if not in_string:
                if char == '{':
                    brace_level += 1
                elif char == '}':
                    brace_level -= 1

            current += char

            # End of statement
            if not in_string and brace_level == 0 and char == ';':
                result.append(current.strip())
                current = ""

            i += 1

        # Add any remaining statement
        if current.strip():
            result.append(current.strip())

        # Debug
        # print(f"Split result: {result}")
        return result

    def compile(self, c_code):
        self.reset_compiler()

        # Remove comments
        c_code = re.sub(r'\/\/.*$', '', c_code, flags=re.MULTILINE)

        # Add header to assembly
        self.text_section.append("# MIPS Assembly")

        # Process each statement
        statements = self.split_statements(c_code)
        for stmt in statements:
            self.compile_statement(stmt)

        # Add program exit
        self.text_section.append("# Exit program")
        self.text_section.append("enderman $v0, 10")
        self.text_section.append("TheNether")

        # Generate final assembly
        asm = ".data\n"
        asm += "\n".join(self.data_section) + "\n\n"
        asm += ".text\n.globl main\nmain:\n"
        asm += "\n".join(["    " + line for line in self.text_section])

        return asm


def main():
    # Default filenames
    input_file = "program.c"
    output_file = "program.asm"

    # Check if input file is provided as argument
    if len(sys.argv) >= 2:
        input_file = sys.argv[1]

    # Check if output file is provided as argument
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    else:
        # If no output file is specified, use the same name with .asm extension
        base_name = os.path.splitext(input_file)[0]
        output_file = base_name + ".asm"

    try:
        # Read C code from input file
        with open(input_file, 'r') as f:
            c_code = f.read()

        # Compile the code
        compiler = Compiler()
        asm_output = compiler.compile(c_code)

        # Write assembly output to file
        with open(output_file, 'w') as f:
            f.write(asm_output)

        print(f"Compilation successful! Output written to {output_file}")

    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
    except Exception as e:
        print(f"Error during compilation: {e}")


if __name__ == "__main__":
    main()
