import re


class Compiler:
    def __init__(self):
        self.reset_compiler()

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
            #self.text_section.append(f"# Declare variable {var_name} at address {self.vars[var_name]['addr']}")

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
        # Debug
        # print(f"Adding string: '{value}'")

        if value not in self.string_data:
            label = f"str_{len(self.string_data)}"
            self.string_data[value] = label

            # Properly process escape sequences for MIPS
            # Keep the string as is - MIPS assembler will handle standard escape sequences
            # Just ensure proper formatting for the .asciiz directive

            self.data_section.append(f'{label}: .asciiz "{value}"')
            # print(f"Added string with label {label}: '{value}'")

        return self.string_data[value]

    def compile_assignment(self, target, value):
        # Add comment
        self.text_section.append(f"# {target} = {value}")

        # Handle constant assignments
        if value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
            reg = self.get_temp_reg()
            self.text_section.append(f"li {reg}, {value}")
            self.text_section.append(f"sw {reg}, {self.get_var_addr(target)}")
        # Handle variable assignments
        elif value in self.vars:
            reg1 = self.get_temp_reg()
            self.text_section.append(f"lw {reg1}, {self.get_var_addr(value)}")
            self.text_section.append(f"sw {reg1}, {self.get_var_addr(target)}")
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
                self.text_section.append(f"li {reg1}, {var1}")
            else:
                self.text_section.append(f"lw {reg1}, {self.get_var_addr(var1)}")

            # Load second operand
            if var2.isdigit() or (var2.startswith('-') and var2[1:].isdigit()):
                self.text_section.append(f"li {reg2}, {var2}")
            else:
                self.text_section.append(f"lw {reg2}, {self.get_var_addr(var2)}")

            self.text_section.append(f"div {reg1}, {reg2}")
            self.text_section.append(f"mfhi {result}")  # Get remainder
            self.text_section.append(f"sw {result}, {self.get_var_addr(target)}")

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
                self.text_section.append(f"li {reg1}, {var1}")
            else:
                self.text_section.append(f"lw {reg1}, {self.get_var_addr(var1)}")

            # Load second operand
            if var2.isdigit() or (var2.startswith('-') and var2[1:].isdigit()):
                self.text_section.append(f"li {reg2}, {var2}")
            else:
                self.text_section.append(f"lw {reg2}, {self.get_var_addr(var2)}")

            self.text_section.append(f"add {result}, {reg1}, {reg2}")
            self.text_section.append(f"sw {result}, {self.get_var_addr(target)}")

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
                self.text_section.append(f"li {reg1}, {var1}")
            else:
                self.text_section.append(f"lw {reg1}, {self.get_var_addr(var1)}")

            # Load second operand
            if var2.isdigit() or (var2.startswith('-') and var2[1:].isdigit()):
                self.text_section.append(f"li {reg2}, {var2}")
            else:
                self.text_section.append(f"lw {reg2}, {self.get_var_addr(var2)}")

            # Branch if not equal (skip the if body)
            self.text_section.append(f"bne {reg1}, {reg2}, {end_label}")

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
                self.text_section.append(f"li {reg1}, {left_var}")
            else:
                self.text_section.append(f"lw {reg1}, {self.get_var_addr(left_var)}")

            if left_val.isdigit() or (left_val.startswith('-') and left_val[1:].isdigit()):
                self.text_section.append(f"li {reg2}, {left_val}")
            else:
                self.text_section.append(f"lw {reg2}, {self.get_var_addr(left_val)}")

            # If first condition fails, skip
            self.text_section.append(f"bne {reg1}, {reg2}, {end_label}")

            # Second condition
            if right_var.isdigit() or (right_var.startswith('-') and right_var[1:].isdigit()):
                self.text_section.append(f"li {reg3}, {right_var}")
            else:
                self.text_section.append(f"lw {reg3}, {self.get_var_addr(right_var)}")

            if right_val.isdigit() or (right_val.startswith('-') and right_val[1:].isdigit()):
                self.text_section.append(f"li {reg4}, {right_val}")
            else:
                self.text_section.append(f"lw {reg4}, {self.get_var_addr(right_val)}")

            # If second condition fails, skip
            self.text_section.append(f"bne {reg3}, {reg4}, {end_label}")

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
                self.text_section.append(f"li {reg1}, {var1}")
            else:
                self.text_section.append(f"lw {reg1}, {self.get_var_addr(var1)}")

            # Load second operand
            if var2.isdigit() or (var2.startswith('-') and var2[1:].isdigit()):
                self.text_section.append(f"li {reg2}, {var2}")
            else:
                self.text_section.append(f"lw {reg2}, {self.get_var_addr(var2)}")

            # Branch if greater or equal (opposite of less than)
            self.text_section.append(f"bge {reg1}, {reg2}, {end_label}")

        # Compile body - splitting compound statements
        for stmt in self.split_compound_statement(body):
            self.compile_statement(stmt)

        # Jump back to start
        self.text_section.append(f"j {start_label}")
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
                self.text_section.append(f"li $v0, 4")
                self.text_section.append(f"la $a0, {label}")
                self.text_section.append(f"syscall")
            else:
                print(f"Warning: Failed to add string: '{value}'")
        elif print_type == 'int':
            self.text_section.append(f"# print_int({value})")
            reg = self.get_temp_reg()

            if value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
                self.text_section.append(f"li {reg}, {value}")
            else:
                addr = self.get_var_addr(value)
                if addr is not None:
                    self.text_section.append(f"lw {reg}, {addr}")
                else:
                    print(f"Warning: Variable '{value}' not declared")
                    return

            self.text_section.append(f"move $a0, {reg}")
            self.text_section.append(f"li $v0, 1")
            self.text_section.append(f"syscall")

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
        self.text_section.append("li $v0, 10")
        self.text_section.append("syscall")

        # Generate final assembly
        asm = ".data\n"
        asm += "\n".join(self.data_section) + "\n\n"
        asm += ".text\n.globl main\nmain:\n"
        asm += "\n".join(["    " + line for line in self.text_section])

        return asm


# Example usage
compiler = Compiler()
c_program = """
int i;
int three;
int five;
int step;
int fizz;
int buzz;
int cond;

three = 3;
five = 5;
step = 1;
i = 1;

while (i < 100) {
    fizz = 0;
    buzz = 0;

    cond = i % three;
    if (cond == 0) {
        fizz = 1;
    }

    cond = i % five;
    if (cond == 0) {
        buzz = 1;
    }

    if (fizz == 1) {
        print_str("Fizz");
    }

    if (buzz == 1) {
        print_str("Buzz");
    }

    if (fizz == 0 && buzz == 0) {
        print_int(i);
    }

    print_str("\\n");
    i = i + step;
}
"""

asm_output = compiler.compile(c_program)
print("Assembly output:")
print(asm_output)

print("Compilation complete.")