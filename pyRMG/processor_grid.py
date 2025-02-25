import random 
import math
import itertools
import numpy as np

def get_min_middle_max_indices(values):
    """Get indices of the minimum, middle, and maximum values in an array of length 3."""
    max_idx, min_idx = np.argmax(values), np.argmin(values)
    if max_idx == min_idx:  # All values are identical
        return 0, 1, 2
    middle_idx = next(iter(set(range(3)) - {max_idx, min_idx}))
    return min_idx, middle_idx, max_idx

def generate_gpu_mapping(value, gpus_per_node=8):
    """Generate possible shifts for GPU distribution based on input grid density values."""
    if value < gpus_per_node:
        return np.arange(0, gpus_per_node - value + 1)  # No reduction in grid density
    low_bound = -1 * (value // gpus_per_node - 1)  # Proportional reduction
    high_bound = gpus_per_node - (value % gpus_per_node)
    return np.arange(low_bound, high_bound + 1)

def weighting_function(x, sigma, x_ideal, alpha=0.2, beta=0.1, tolerance=1e-1):
    """Compute the weighting function to optimize GPU mapping selection."""
    penalty = (alpha if x < x_ideal else beta) * (x - x_ideal) ** 2 + x_ideal
    return penalty * sigma if sigma > tolerance else penalty * tolerance # Avoid issues with zero sigma

def evaluate_combination(original_integers, combination, grid_values, min_idx, mid_idx, max_idx,
                         target_nodes, gpus_per_node, division_limit=15):
    """Evaluate a specific GPU distribution combination and compute its weighted value."""
    additions = np.zeros(3, dtype=int)
    additions[[max_idx, mid_idx, min_idx]] = combination

    new_combo = original_integers + additions
    if 0 in new_combo:  # Avoid division by zero
        return None, None

    total_gpus = math.prod(new_combo)
    if total_gpus <= gpus_per_node: # Allow partial gpus_per_node for single node jobs
        pass
    else:
        if total_gpus % gpus_per_node != 0:  # Ensure divisibility
            return None, None

    grid_per_combo = grid_values / new_combo
    if not all(x >= division_limit for x in grid_per_combo): # Helps with number of grid points per PE >= kohn_sham_fd_order/2 
        return None, None

    sigma = np.std(grid_per_combo)
    target_gpus = target_nodes * gpus_per_node
    weighted_value = weighting_function(total_gpus, sigma, target_gpus)

    return new_combo.tolist(), weighted_value

def find_best_divisible_combination(grid_values, original_integers, combinations,
                                    min_idx, mid_idx, max_idx, target_nodes, gpus_per_node):
    """Find the optimal GPU distribution that minimizes the weighting function."""
    best_combo, best_value = None, float('inf')

    for combo in combinations:
        new_combo, weighted_value = evaluate_combination(original_integers, combo, grid_values,
                                                         min_idx, mid_idx, max_idx,
                                                         target_nodes, gpus_per_node)
        if new_combo and weighted_value < best_value:
            best_value = weighted_value
            best_combo = new_combo

    return best_combo, best_value if best_value != float('inf') else None

def get_processor_grid(grid_values, target_nodes, gpus_per_node=8):
    """Determine the optimal processor grid distribution given grid values and constraints."""
    normalized_grid = np.array(grid_values) / np.min(grid_values)
    min_idx, mid_idx, max_idx = get_min_middle_max_indices(normalized_grid)
    max_lowest_grid_gpus = int(np.ceil((target_nodes * gpus_per_node) ** (1/3)))

    best_processor_grid, best_function_value = [1, 1, 1], weighting_function(x=1,
                                                                             sigma=np.std(grid_values),
                                                                             x_ideal=target_nodes * gpus_per_node)

    while max_lowest_grid_gpus > 0:
        rounded_values = np.round(normalized_grid * max_lowest_grid_gpus).astype(int)
        total_gpus = math.prod(rounded_values)

        max_shifts = generate_gpu_mapping(rounded_values[max_idx], gpus_per_node)
        mid_shifts = generate_gpu_mapping(rounded_values[mid_idx], gpus_per_node)
        min_shifts = np.array([-1, 0, 1])

        combinations = itertools.product(max_shifts, mid_shifts, min_shifts)

        best_combo, best_value = find_best_divisible_combination(
            grid_values, rounded_values, combinations, min_idx, mid_idx, max_idx,
            target_nodes, gpus_per_node
        )

        if best_value is not None and best_value < best_function_value:
            best_processor_grid, best_function_value = best_combo, best_value

        max_lowest_grid_gpus -= 1

    total_nodes = int(math.prod(best_processor_grid) / gpus_per_node)
    if total_nodes == 0: # In case this is equal to 0, for small jobs with partial nodes
        total_nodes = 1
    best_processor_grid_string = ' '.join([str(gpus) for gpus in best_processor_grid])

    return best_processor_grid_string, total_nodes

