import itertools
import random

def generate_city_partitions(num_cities, num_salesmen):
    city_groups = []
    cities = list(range(1, num_cities + 1))
    group_size = num_cities // num_salesmen
    
    for i in range(num_salesmen - 1):
        group = cities[i * group_size:(i + 1) * group_size]
        city_groups.append(group)

    # Add remaining cities to the last group
    city_groups.append(cities[(num_salesmen - 1) * group_size:])

    return city_groups

def generate_permutations(city_groups, num_samples):
    sampled_permutations = []
    for group in city_groups:
        group_permutations = list(itertools.permutations(group))
        sampled_permutations.append(random.sample(group_permutations, num_samples))
    return sampled_permutations

def combine_permutations(sampled_permutations):
    combined_permutations = list(itertools.product(*sampled_permutations))
    return combined_permutations

def generate_initial_population(num_cities, num_salesmen, num_samples):
    city_groups = generate_city_partitions(num_cities, num_salesmen)
    sampled_permutations = generate_permutations(city_groups, num_samples)
    initial_population = combine_permutations(sampled_permutations)
    return initial_population

if __name__ == "__main__":
    # Example: 9 cities, 3 salesmen, 3 samples per group
    num_cities = 9
    num_salesmen = 3
    num_samples = 2

    initial_population = generate_initial_population(num_cities, num_salesmen, num_samples)
    for item in initial_population:
        print(initial_population)
