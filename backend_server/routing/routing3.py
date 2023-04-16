import numpy as np
import random
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans

rng = np.random.default_rng(2023)
random.seed(2023)

class Individual:

    def __init__(self):
        self.fitness = np.inf
        self.solution = []

## Problem Parameters

# Generate random cities and distance matrix
cities = [
    [2.00, 1.00], # Depot

    [1.00, 1.00],
    [0.75, 1.00],
    [0.50, 1.00],

    [2.00, 2.00],
    [2.00, 2.25],
    [2.00, 2.50],

    [3.00, 1.0],
    [3.25, 1.0],
    [3.50, 1.0],
]
n_cities = len(cities)
n_salesmen = 3
dist_matrix = np.array([[np.sqrt((c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2)
                         for c1 in cities] for c2 in cities])


# GA parameters
population_size = 15
generations = 20
mutation_rate = 0.1
elitism = True





# def create_individual_clustering(clusters, n_salesmen):
#     # print(dir(clusters))
#     # print(clusters.labels_)
#     routes = [[] for _ in range(n_salesmen)]
#     for i, cluster in enumerate(clusters):
#         cluster_cities = [city_idx for city_idx, label in enumerate(cluster.labels_) if label == i]
#         random.shuffle(cluster_cities)
#         for j in range(n_salesmen):
#             routes[j].extend(cluster_cities[j::n_salesmen])
#     return routes
def create_individual_clustering(labels, n_salesmen):
    n_clusters = len(set(labels))
    routes = [[] for _ in range(n_salesmen)]
    for i in range(n_clusters):
        cluster_cities = [city_idx + 1 for city_idx, label in enumerate(labels) if label == i]
        random.shuffle(cluster_cities)
        for j in range(n_salesmen):
            routes[j].extend(cluster_cities[j::n_salesmen])
        
    individual = Individual()
    individual.solution = routes
    return individual

# def initial_population_kmeans(population_size, n_cities, n_salesmen, city_coords):
#     clusters = KMeans(n_clusters=n_salesmen).fit(city_coords[1:]) # 1st coords is depot!
#     population = [create_individual_clustering(clusters, n_salesmen) for _ in range(population_size)]
#     return population

def initial_population_kmeans(population_size, n_salesmen, city_coords):
    kmeans = KMeans(n_clusters=n_salesmen).fit(city_coords[1:])
    population = [create_individual_clustering(kmeans.labels_, n_salesmen) for _ in range(population_size)]
    return population





# Helper functions
def create_individual():
    route = list(range(1, n_cities))
    random.shuffle(route)
    partition_points = sorted(random.sample(route[:-1], n_salesmen - 1))
    individual = Individual()
    individual.solution = [route[i:j] for i, j in zip([0] + partition_points, partition_points + [None])]
    return individual

def fitness(individual):
    total_distance = 0.0
    for route in individual:
        # print(route)
        if len(route) == 0:
            distance = np.inf
        else:
            distance = dist_matrix[0][route[0]] + dist_matrix[route[-1]][0]
            for i in range(1, len(route)):
                distance += dist_matrix[route[i-1]][route[i]]
        total_distance += distance
    return total_distance

def order_crossover(parent1, parent2):
    child = []

    p1_flattened = [city for route in parent1.solution for city in route]
    p2_flattened = [city for route in parent2.solution for city in route]

    start = random.randint(0, len(p1_flattened) - 1)
    end = random.randint(start, len(p1_flattened))

    child_route = p1_flattened[start:end]
    p2_remaining = [city for city in p2_flattened if city not in child_route]

    child_flattened = p2_remaining[:start] + child_route + p2_remaining[start:]

    partition_points = sorted(random.sample(range(1, len(child_flattened)), n_salesmen - 1))

    child = [child_flattened[i:j] for i, j in zip([0] + partition_points, partition_points + [None])]

    individual = Individual()
    individual.solution = child
    # return child
    return individual

def mutate(individual, mutation_rate):
    routes = individual.solution.copy()
    for route in routes:
        for i in range(len(route)):
            if random.random() < mutation_rate:
                swap_index = random.randint(0, len(route) - 1)
                route[i], route[swap_index] = route[swap_index], route[i]
    new_individual = Individual()
    new_individual.solution = routes
    new_individual.fitness = fitness(new_individual.solution) 
    # return individual
    return new_individual

# def selection(population):
#     # sorted_population = sorted(population, key=lambda x: fit_scores[x], reverse=True)
#     # sorted_population = sorted(population, key=lambda x: x.fitness, reverse=True)
#     sorted_population = sorted(population, key=lambda x: x.fitness, reverse=False)
#     return sorted_population[:population_size]


def selection(parent_population, child_population):
    # sorted_population = sorted(parent_population + child_population, key=lambda x: x.fitness, reverse=False)
    # elite = [min(parent_population, key=lambda x: x.fitness) if elitism else []]
    # return elite + sorted_population[:population_size - len(elite)]

    sorted_population = sorted(parent_population + child_population, key=lambda x: x.fitness, reverse=False)
    # elite = [min(parent_population, key=lambda x: x.fitness) if elitism else []]
    # return elite + 
    return sorted_population[:population_size]


def main():
    # Initialize population

    # - Random
    population0 = [create_individual() for _ in range(population_size//2)]
    # - Clustering
    population1 = initial_population_kmeans(population_size//2, n_salesmen, cities)

    population = population0 + population1 
    print("Population size: ", len(population))

    # Main loop
    for gen in range(generations):
        # Calculate the fitness of each individual in the population
        for individual in population:
            individual.fitness = fitness(individual.solution) 
       
        # Crossover
        children = []
        while len(children) < population_size:
            parent1 = random.choice(population)
            parent2 = random.choice(population)
            if parent1 != parent2:
                child = order_crossover(parent1, parent2)
                children.append(child)

        # Mutation
        for i in range(len(children)):
            children[i] = mutate(children[i], mutation_rate)
        
        # Selection
        population = selection(population, children)
       
        # Print best individual
        best_individual = min(population, key=lambda x: x.fitness)

        print(f"Generation {gen + 1}: Best fitness  = {fitness(best_individual.solution)}")
        print(f"                    : Best solution = {best_individual.solution}")
        print()
    
    a = Individual()
    a.solution = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    # a.solution = [[1], [2], [3], [4], [5], [6]]
    print()
    print(f"Known Best Fitness  = {fitness(a.solution)}")
    print(f"Known Best Solution = {a.solution}")
    print()





if __name__ == "__main__":
    main()
    # population = initial_population_kmeans(population_size, n_cities, n_salesmen, cities)
    # print(population)
    # print(initial_population(population_size, n_cities, n_salesmen))
    # plt.scatter([x[0] for x in cities], [x[1] for x in cities])
    # plt.show()

