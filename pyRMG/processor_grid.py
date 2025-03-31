import random 
import math
import itertools
import numpy as np

def get_min_middle_max_indices(values):
    """Get indices of the minimum, middle, and maximum values in an array of length 3."""
    max_idx, min_idx = np.argmax(values), np.argmin(values)
    if max_idx == min_idx:  # If all values are the same
        return 0, 1, 2
    middle_idx = next(iter(set(range(3)) - {max_idx, min_idx}))
    return min_idx, middle_idx, max_idx

def generate_gpu_mapping(value, gpus_per_node=8):
    """Generate possible shifts for GPU distribution based on input grid density values."""
    if value < gpus_per_node:
        return np.arange(0, gpus_per_node - value + 1)
    
    low_bound = -1 * (value // gpus_per_node - 1)
    high_bound = gpus_per_node - (value % gpus_per_node)
    
    return np.arange(low_bound, high_bound + 1)

def weighting_function(x, sigma, x_ideal, alpha=0.2, beta=0.1, tolerance=1e-1):
    """Compute the weighting function to optimize GPU mapping selection."""
    penalty_factor = alpha if x < x_ideal else beta
    penalty = penalty_factor * (x - x_ideal) ** 2 + x_ideal
    return penalty * max(sigma, tolerance)  # Prevent zero sigma issues

def evaluate_combination(grid_values, modified_grid, min_idx, mid_idx, max_idx,
                         target_nodes, gpus_per_node, division_limit=8):
    """Evaluate a specific GPU distribution combination and compute its weighted value."""
    total_gpus = np.prod(modified_grid)
    
    if 0 in modified_grid: # or total_gpus % gpus_per_node != 0:
        return None, None  # Invalid configuration
    
    # New division limit check 
    if not total_gpus % division_limit == 0:
        return None, None
    
    # Old division limit check
    #per_grid_density = grid_values / modified_grid
    #if not all(x >= division_limit for x in per_grid_density):
    #    return None, None  # Fails grid density constraint
    
    per_grid_density = grid_values / modified_grid
    sigma = np.std(per_grid_density)
    target_gpus = target_nodes * gpus_per_node
    weighted_value = weighting_function(total_gpus, sigma, target_gpus)

    return modified_grid.tolist(), weighted_value

def find_best_divisible_combination(grid_values, initial_grid, combinations,
                                    min_idx, mid_idx, max_idx, target_nodes, gpus_per_node):
    """Find the optimal GPU distribution that minimizes the weighting function."""
    best_combo, best_value = None, float('inf')

    for combo in combinations:
        modified_grid = initial_grid + np.array([combo[max_idx], combo[mid_idx], combo[min_idx]])
        new_combo, weighted_value = evaluate_combination(
            grid_values, modified_grid, min_idx, mid_idx, max_idx, target_nodes, gpus_per_node
        )
        
        if new_combo and weighted_value < best_value:
            best_value = weighted_value
            best_combo = new_combo

    return best_combo, best_value if best_value != float('inf') else None

def get_processor_grid(grid_values, target_nodes, gpus_per_node=8, kpoint_distribution=1):
    """
    Determine the optimal processor grid distribution given grid values and constraints.

    :param grid_values: 3D grid values representing x, y, and z processor grid densities.
    :param target_nodes: Total number of desired nodes.
    :param gpus_per_node: Number of GPUs per node.
    :param kpoint_distribution: How to distribute over kpoints. 
    :return: Optimal processor grid as a string and required number of nodes.
    """
    # Normalize grid values based on the smallest grid size
    normalized_grid = np.array(grid_values) / np.min(grid_values)
    min_idx, mid_idx, max_idx = get_min_middle_max_indices(normalized_grid)
    
    # Set the upper limit for the lowest processor grid dimension
    max_grid_factor = int(np.ceil((target_nodes * gpus_per_node) ** (1/3)))
    
    # Initialize best processor grid
    best_processor_grid = np.floor(normalized_grid).astype(int)
    best_function_value = weighting_function(
        x=np.prod(best_processor_grid), sigma=np.std(grid_values), x_ideal=target_nodes * gpus_per_node
    )

    #print(best_processor_grid, best_function_value)
    while max_grid_factor > 0:
        # Generate candidate grid by scaling normalized grid
        candidate_grid = np.round(normalized_grid * max_grid_factor).astype(int)
        total_gpus = np.prod(candidate_grid)

        # Generate possible shifts for GPU allocation
        max_shifts = generate_gpu_mapping(candidate_grid[max_idx], gpus_per_node)
        mid_shifts = generate_gpu_mapping(candidate_grid[mid_idx], gpus_per_node)
        min_shifts = np.array([-1, 0, 1])  # Small adjustments

        # Generate all possible shift combinations
        combinations = itertools.product(max_shifts, mid_shifts, min_shifts)

        # Find the best valid GPU grid configuration
        best_combo, best_value = find_best_divisible_combination(
            grid_values, candidate_grid, combinations, min_idx, mid_idx, max_idx,
            target_nodes, gpus_per_node
        )

        # Update best configuration if improvement is found
        if best_value is not None and best_value < best_function_value:
            best_processor_grid, best_function_value = best_combo, best_value
        #print(best_processor_grid, best_function_value)
        max_grid_factor -= 1  # Reduce search space

    # Compute required number of nodes
    total_nodes = max(1, math.ceil((kpoint_distribution * np.prod(best_processor_grid)) / gpus_per_node))

    return ' '.join(map(str, best_processor_grid)), total_nodes

