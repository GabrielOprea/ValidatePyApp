import pickle
import git
import os
import ast
import re
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

def compute_max_nesting_depth(file_content):
    try:
        tree = ast.parse(file_content)
    except SyntaxError:
        return 0

    max_depth = 0

    def visit_node(node, depth=0):
        nonlocal max_depth
        max_depth = max(max_depth, depth)
        for child in ast.iter_child_nodes(node):
            visit_node(child, depth + 1)

    visit_node(tree)
    return max_depth

def compute_avg_nesting_depth_without_ast(code):
    indentation_levels = []
    
    for line in code.splitlines():
        stripped_line = line.lstrip()
        
        if not stripped_line or stripped_line.startswith("#"):
            continue
        
        indentation_level = len(line) - len(stripped_line)
        indentation_levels.append(indentation_level)

    if indentation_levels:
        avg_nesting = sum(indentation_levels) / len(indentation_levels)
        return avg_nesting / 4
    return 0

def compute_naming_convention_ratios(code):
    snake_case_pattern = re.compile(r'\b[a-z]+(?:_[a-z]+)+\b')
    camel_case_pattern = re.compile(r'\b[a-z]+(?:[A-Z][a-z]*)+\b')
    
    snake_case_count = len(snake_case_pattern.findall(code))
    camel_case_count = len(camel_case_pattern.findall(code))
    
    total_variables = snake_case_count + camel_case_count

    snake_ratio = snake_case_count / total_variables if total_variables > 0 else 0
    camel_ratio = camel_case_count / total_variables if total_variables > 0 else 0

    result = {
        "snake_case_ratio": snake_ratio,
        "camel_case_ratio": camel_ratio
    }
    return result

def compute_avg_indentation(file_content):
    lines = file_content.splitlines()
    indentation_levels = []

    for line in lines:
        stripped_line = line.lstrip()
        if stripped_line:
            indentation_levels.append(len(line) - len(stripped_line))

    return np.mean(indentation_levels) if indentation_levels else 0

def compute_variable_naming_metrics(file_content):
    snake_case = 0
    camel_case = 0
    total_variables = 0

    try:
        tree = ast.parse(file_content)
    except SyntaxError:
        return {"snake_case_ratio": 0, "camel_case_ratio": 0}

    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            total_variables += 1
            if re.match(r"^[a-z]+(_[a-z]+)+$", node.id):
                snake_case += 1
            elif re.match(r"^[a-z]+([A-Z][a-z]*)+$", node.id):
                camel_case += 1

    if total_variables == 0:
        return {"snake_case_ratio": 0, "camel_case_ratio": 0}

    return {
        "snake_case_ratio": snake_case / total_variables,
        "camel_case_ratio": camel_case / total_variables,
    }

def calculate_features(commit):
    avg_nesting_depths = []
    avg_indentation_levels = []
    snake_case_ratios = []
    camel_case_ratios = []

    for file in commit["files_changed"]:

        file_content = get_total_diff([file])
        avg_nesting_depths.append(compute_avg_nesting_depth_without_ast(file_content))
        avg_indentation_levels.append(compute_avg_indentation(file_content))
        naming_metrics = compute_naming_convention_ratios(file_content)
        snake_case_ratios.append(naming_metrics["snake_case_ratio"])
        camel_case_ratios.append(naming_metrics["camel_case_ratio"])

    return {
        "avg_nesting_depth": np.mean(avg_nesting_depths) if avg_nesting_depths else 0,
        "avg_indentation": np.mean(avg_indentation_levels) if avg_indentation_levels else 0,
        "snake_case_ratio": np.mean(snake_case_ratios) if snake_case_ratios else 0,
        "camel_case_ratio": np.mean(camel_case_ratios) if camel_case_ratios else 0,
    }

def get_total_diff(files_changed):
    total_diff = ""
    for file in files_changed:
        total_diff += file["diff"] + "\n"
    total_diff = total_diff.replace("\ No newline at end of file", "")

    lines = total_diff.splitlines()
    cleaned_lines = []

    for line in lines:
        if not line.strip().startswith('@@'):
            cleaned_line = re.sub(r"^[-+]", " ", line)
            cleaned_lines.append(cleaned_line)

    total_diff =  "\n".join(cleaned_lines)
    return total_diff
