import streamlit as st
import random
from fractions import Fraction


# --- Helper Functions ---
def format_latex(f: Fraction):
    """Formats a Fraction object into a LaTeX string."""
    if f.denominator == 1:
        return f"{f.numerator}"
    if f < 0:
        return f"-\\frac{{{abs(f.numerator)}}}{{{f.denominator}}}"
    return f"\\frac{{{f.numerator}}}{{{f.denominator}}}"


def get_op_latex(op):
    return {"+": "+", "-": "-", "*": "\\times", "/": "\\div"}[op]


def generate_fraction():
    """Generates a random non-zero fraction."""
    num = random.randint(1, 7)

    # Multiply by -1 or 1 only if negatives are allowed
    if st.session_state.get("allow_negatives", True):
        num *= random.choice([-1, 1])

    den = random.randint(2, 7)
    return Fraction(num, den)


def evaluate_expression(fracs, ops):
    """Evaluates a list of fractions and operators using order of operations."""
    if len(fracs) == 2:
        if ops[0] == '+': return fracs[0] + fracs[1]
        if ops[0] == '-': return fracs[0] - fracs[1]
        if ops[0] == '*': return fracs[0] * fracs[1]
        if ops[0] == '/': return fracs[0] / fracs[1]
    elif len(fracs) == 3:
        # PEMDAS: Do multiplication/division first
        if ops[1] in ['*', '/'] and ops[0] in ['+', '-']:
            right_val = evaluate_expression([fracs[1], fracs[2]], [ops[1]])
            return evaluate_expression([fracs[0], right_val], [ops[0]])
        else:
            left_val = evaluate_expression([fracs[0], fracs[1]], [ops[0]])
            return evaluate_expression([left_val, fracs[2]], [ops[1]])


def evaluate_left_to_right_mistake(fracs, ops):
    """Evaluates ignoring PEMDAS (strictly left to right) to catch mistakes."""
    if len(fracs) == 3:
        left_val = evaluate_expression([fracs[0], fracs[1]], [ops[0]])
        return evaluate_expression([left_val, fracs[2]], [ops[1]])
    return None


def setup_new_problem():
    """Generates a new problem based on sidebar settings and saves to state."""
    available_ops = st.session_state.get("selected_ops", ["+", "-", "*", "/"])
    if not available_ops:
        available_ops = ["+", "-", "*", "/"]  # Fallback

    mode = st.session_state.get("problem_mode", "Single Operation")
    term_count = 3 if mode == "Multi-step (3 fractions)" else 2

    fracs = [generate_fraction() for _ in range(term_count)]
    ops = [random.choice(available_ops) for _ in range(term_count - 1)]

    st.session_state.fracs = fracs
    st.session_state.ops = ops
    st.session_state.ans = evaluate_expression(fracs, ops)
    st.session_state.checked = False
    st.session_state.user_input = ""

    st.session_state.current_input = ""


# --- Step-by-Step Renderers ---
def show_add_sub_steps(f1, f2, op):
    """Renders LaTeX steps for addition and subtraction."""
    step1 = f"{format_latex(f1)} {op} {format_latex(f2)}"

    if f1.denominator == f2.denominator:
        st.write("**Step: Denominators are already the same. Combine the numerators.**")
        combined_num = f"{f1.numerator} {op} {f2.numerator}"
        step2 = f"\\frac{{{combined_num}}}{{{f1.denominator}}}"
        st.latex(f"{step1} = {step2} = {format_latex(evaluate_expression([f1, f2], [op]))}")
    else:
        st.write("**Step 1: Find a common denominator by multiplying the denominators.**")
        common_den = f1.denominator * f2.denominator
        new_num1 = f1.numerator * f2.denominator
        new_num2 = f2.numerator * f1.denominator

        c_f1 = f"\\frac{{{f1.numerator} \\times {f2.denominator}}}{{{f1.denominator} \\times {f2.denominator}}}"
        c_f2 = f"\\frac{{{f2.numerator} \\times {f1.denominator}}}{{{f2.denominator} \\times {f1.denominator}}}"

        st.latex(f"{step1} \\rightarrow {c_f1} {op} {c_f2}")

        st.write("**Step 2: Combine the new numerators over the common denominator.**")
        step3 = f"\\frac{{{new_num1} {op} {new_num2}}}{{{common_den}}}"
        raw_ans = Fraction(new_num1 + new_num2 if op == '+' else new_num1 - new_num2, common_den)

        st.latex(f"= {step3} = \\frac{{{new_num1 + new_num2 if op == '+' else new_num1 - new_num2}}}{{{common_den}}}")

        if raw_ans.denominator != common_den or raw_ans.denominator == 1:
            st.latex(f"= {format_latex(raw_ans)} \\text{{ (Simplified)}}")


def show_mult_div_steps(f1, f2, op):
    """Renders LaTeX steps for multiplication and division."""
    if op == "*":
        step1 = f"{format_latex(f1)} \\times {format_latex(f2)}"
        num_expr = f"{f1.numerator} \\times {f2.numerator}"
        den_expr = f"{f1.denominator} \\times {f2.denominator}"
        step2 = f"\\frac{{{num_expr}}}{{{den_expr}}}"

        raw_num = f1.numerator * f2.numerator
        raw_den = f1.denominator * f2.denominator
        step3 = f"\\frac{{{raw_num}}}{{{raw_den}}}"

        st.latex(f"{step1} = {step2} = {step3}")

        correct_ans = f1 * f2
        if Fraction(raw_num, raw_den) != correct_ans or raw_den < 0:
            st.latex(f"= {format_latex(correct_ans)} \\text{{ (Simplified)}}")

    elif op == "/":
        reciprocal = Fraction(f2.denominator, f2.numerator)
        step1 = f"{format_latex(f1)} \\div {format_latex(f2)}"
        st.write("**Step 1: Rewrite as multiplication by the reciprocal (flip the second fraction)**")
        step2 = f"{format_latex(f1)} \\times {format_latex(reciprocal)}"
        st.latex(f"{step1} = {step2}")

        st.write("**Step 2: Multiply straight across**")
        show_mult_div_steps(f1, reciprocal, "*")


# --- App Initialization ---
st.set_page_config(page_title="Fraction Master", page_icon="➗")
st.markdown("""
    <style>
    .katex-html {
        padding-top: 1em;
        padding-bottom: 1em;
    }
    </style>
""", unsafe_allow_html=True)

# --- Sidebar Customization ---
st.sidebar.header("⚙️ Customization")

st.sidebar.checkbox("Include Negative Fractions", value=True, key="allow_negatives", on_change=setup_new_problem)

st.sidebar.multiselect("Operations to Include", ["+", "-", "*", "/"], default=["+", "-", "*", "/"], key="selected_ops",
                       on_change=setup_new_problem)
st.sidebar.radio("Problem Type", ["Single Operation", "Multi-step (3 fractions)"], key="problem_mode",
                 on_change=setup_new_problem)

if "fracs" not in st.session_state or not st.session_state.get("selected_ops"):
    if not st.session_state.get("selected_ops"):
        st.sidebar.warning("Please select at least one operation!")
    else:
        setup_new_problem()

# --- UI Header ---
st.title("➗ Fraction Master")
st.write("Test your skills! Enter your answers as simple fractions (e.g., `-3/4` or `2` or `5/2`).")
st.markdown("---")

# --- Display Current Problem ---
if "fracs" in st.session_state and st.session_state.get("selected_ops"):
    fracs = st.session_state.fracs
    ops = st.session_state.ops

    # Build problem LaTeX string
    prob_latex = format_latex(fracs[0])
    for i, op in enumerate(ops):
        prob_latex += f" {get_op_latex(op)} {format_latex(fracs[i + 1])}"
    prob_latex += " = ?"

    st.subheader("Solve:")
    st.latex(prob_latex)

    # --- User Input & Form ---
    with st.form("quiz_form"):
        user_input = st.text_input("Your Answer:", key="current_input")
        submit = st.form_submit_button("Check Answer")

    if submit:
        if user_input.strip() == "":
            st.warning("Please enter an answer before submitting.")
        else:
            st.session_state.user_input = user_input.strip()
            st.session_state.checked = True

    # --- Evaluation and Feedback ---
    if st.session_state.checked:
        user_str = st.session_state.user_input
        correct_ans = st.session_state.ans

        try:
            user_frac = Fraction(user_str)

            # 1. Correct Answer
            if user_frac == correct_ans:
                st.success("🎉 **Correct!** Great job.")
                st.button("Next Problem", on_click=setup_new_problem)

            else:
                # 2. Diagnose Mistakes
                st.error("Not quite. Let's look at what might have happened.")

                # Check for Common Mistakes
                mistake_found = False

                # Mistake: Sign Error
                if abs(user_frac) == abs(correct_ans):
                    st.info(
                        "💡 **Diagnosis: Sign Error** \nYou got the numbers right, but the positive/negative sign is incorrect.")
                    mistake_found = True

                # Mistake: Added/Subtracted Denominators (Single Step)
                elif len(fracs) == 2 and ops[0] in ["+", "-"]:
                    bad_num = fracs[0].numerator + (fracs[1].numerator if ops[0] == "+" else -fracs[1].numerator)
                    bad_den = fracs[0].denominator + fracs[1].denominator
                    if bad_den != 0 and user_frac == Fraction(bad_num, bad_den):
                        st.info(
                            "💡 **Diagnosis: Added Denominators** \nYou added or subtracted the denominators straight across. Remember, you must find a common denominator and ONLY add/subtract the numerators!")
                        mistake_found = True

                # Mistake: Ignored PEMDAS (Multi-step)
                elif len(fracs) == 3:
                    wrong_pemdas_ans = evaluate_left_to_right_mistake(fracs, ops)
                    if wrong_pemdas_ans is not None and user_frac == wrong_pemdas_ans and correct_ans != wrong_pemdas_ans:
                        st.info(
                            "💡 **Diagnosis: Order of Operations Error (PEMDAS)** \nYou calculated strictly left-to-right. Remember that multiplication and division must be done BEFORE addition and subtraction!")
                        mistake_found = True

                if not mistake_found:
                    st.info(
                        "💡 **Diagnosis: Calculation Error** \nIt looks like there was a math error in finding a common denominator, simplifying, or applying the operations.")

                # 3. Show Step-by-Step Solution
                st.markdown("### Step-by-Step Solution")

                if len(fracs) == 2:
                    if ops[0] in ["+", "-"]:
                        show_add_sub_steps(fracs[0], fracs[1], ops[0])
                    else:
                        show_mult_div_steps(fracs[0], fracs[1], ops[0])

                elif len(fracs) == 3:
                    st.write("**Step 1: Order of Operations (PEMDAS)**")

                    if ops[1] in ['*', '/'] and ops[0] in ['+', '-']:
                        st.write("We must do the multiplication/division on the right side *first*.")
                        right_ans = evaluate_expression([fracs[1], fracs[2]], [ops[1]])
                        st.latex(
                            f"\\text{{Solve: }} {format_latex(fracs[1])} {get_op_latex(ops[1])} {format_latex(fracs[2])} = {format_latex(right_ans)}")

                        st.write("**Step 2: Solve the remaining equation**")
                        st.latex(
                            f"\\text{{New Equation: }} {format_latex(fracs[0])} {get_op_latex(ops[0])} {format_latex(right_ans)}")
                        if ops[0] in ["+", "-"]:
                            show_add_sub_steps(fracs[0], right_ans, ops[0])
                        else:
                            show_mult_div_steps(fracs[0], right_ans, ops[0])

                    else:
                        st.write(
                            "Calculate the left side first (following left-to-right for same-precedence, or doing multiplication/division before addition/subtraction).")
                        left_ans = evaluate_expression([fracs[0], fracs[1]], [ops[0]])
                        st.latex(
                            f"\\text{{Solve: }} {format_latex(fracs[0])} {get_op_latex(ops[0])} {format_latex(fracs[1])} = {format_latex(left_ans)}")

                        st.write("**Step 2: Solve the remaining equation**")
                        st.latex(
                            f"\\text{{New Equation: }} {format_latex(left_ans)} {get_op_latex(ops[1])} {format_latex(fracs[2])}")
                        if ops[1] in ["+", "-"]:
                            show_add_sub_steps(left_ans, fracs[2], ops[1])
                        else:
                            show_mult_div_steps(left_ans, fracs[2], ops[1])

                st.button("Try Another Problem", on_click=setup_new_problem)

        except ValueError:
            st.error("⚠️ Invalid format! Please enter a valid fraction like `-3/4`, `1/2`, or `5`.")
