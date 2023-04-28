import logging
import abc
import pprint
import numpy
import random
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from typing import List 

# from itertools import combinations
# from sympy.combinatorics import Permutation, PermutationGroup

rng = numpy.random.default_rng(2023)
random.seed(2023)



class MTSP:

    def __init__(self, city_coordinates: list[list[float]], num_salesmen: int, precompute_distances: bool = True):
        # Set the given city coordinates
        self.city_coordinates: list[list[float]] = city_coordinates
        # Set the total number of cities to visit
        self.num_cities: int = len(city_coordinates)
        # Set the given number of salesmen that should be coordinated and routed between the cities
        self.num_salesmen: int = num_salesmen
        # Pre-compute the distances between the given cities
        if precompute_distances is True:
            self._distance_matrix = self._precompute_distances()
        else:
            self._distance_matrix = None
        # Validate the given input
        self._validate()

    def _validate(self):
        # Make sure that at least one depot and a city is given in the list
        if len(self.city_coordinates) < 2:
            raise ValueError()
        else:
            # Make sure that a tuple of coordinates is given for each location
            for pair in self.city_coordinates:
                if len(pair) != 2:
                    raise ValueError()
        # Make sure that at least one salesman can be routed between the locations
        if self.num_salesmen < 1:
            raise ValueError()


    def _precompute_distances(self) -> list[list[float]]:
        return [
            [numpy.sqrt((c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2) for c1 in self.city_coordinates]
            for c2 in self.city_coordinates
        ]

    
    def distance(self, city_a: int, city_b: int) -> float:
        if self._distance_matrix is not None:
            return self._distance_matrix[city_a][city_b]
        else:
            return numpy.sqrt(
                (self.city_coordinates[city_a][0] - self.city_coordinates[city_b][0]) ** 2 + \
                (self.city_coordinates[city_a][1] - self.city_coordinates[city_b][1]) ** 2
            )



class Individual:

    def __init__(self, chromosome: list[list[int]], generation: int):
        # Solution representation:
        # - Assume that a multipart chromosome is used
        self.chromosome: list[list[int]] = chromosome
        # The corresponding fitness value of the solution
        self.fitness: None | float = None
        self.generation: int = generation

    def pprint(self):
        # Explicitly write out the chomosome when the 'Individual' object is printed
        string = super().__str__()
        if self.chromosome is not None:
            string = string + " = \n" + 0 * " " + "[\n"
            for part in self.chromosome:
                string += 4 * " " + str(part) + ",\n"
            string += 0 * " " + "]"
            return string
        else:
            return string + " = None"

    def _validate(self):
        if self.chromosome is not None:
            if len(self.chromosome) > 0:
                raise ValueError(f"{self.chromosome}")


class Population:
    
    def __init__(self, individuals: list[Individual]):#, fitness_function_instance: "BaseFitnessFunction"):
        self.individuals: list[Individual] = individuals
        # self.fitness_function_instance: BaseFitnessFunction = fitness_function_instance

    # def evaluate(self):
    #     for individual in self.individuals:
    #         individual.fitness = self.fitness_function_instance.evaluate(individual)

    def pprint(self):
        string = ""
        for inividual in self.individuals:
            string += inividual.__str__() + "\n"
        return string

    def __len__(self) -> int:
        return len(self.individuals)

    def __getitem__(self, item) -> Individual:
        return self.individuals[item]

    def __add__(self, other_population):
        return Population(self.individuals + other_population.individuals)

    def random_pick(self) -> Individual:
        return random.choice(self.individuals)

    def size(self) -> int:
        return len(self.individuals)
    
    def sort(self, reverse: bool = False):
        sorted_population = sorted(
            self.individuals,
            key=lambda x: x.fitness,
            reverse=reverse,
        )
        self.individuals = sorted_population
    
    def prune(self, population_size: int, reverse: bool = False):
        self.sort(reverse=reverse)
        self.individuals = self.individuals[:population_size]

    def get_topk(self, k: int = 1) -> list[Individual]:
        return self.individuals[:k]

class BaseFitnessFunction(abc.ABC):

    def __init__(self):
        pass

    @abc.abstractmethod
    def evaluate(self, individual: Individual):
        pass


class FitnessFunctionMinimizeDistance(BaseFitnessFunction):

    def __init__(self, mtsp_instance: MTSP):
        super().__init__()
        self.mtsp_instance: MTSP = mtsp_instance

    def evaluate(self, individual: Individual) -> Individual:
        total_distance = 0.0
        for route in individual.chromosome:
            if len(route) == 0:
                distance = numpy.inf
            else:
                distance = self.mtsp_instance._distance_matrix[0][route[0]] + self.mtsp_instance._distance_matrix[route[-1]][0]
                for i in range(1, len(route)):
                    distance += self.mtsp_instance._distance_matrix[route[i-1]][route[i]]
            total_distance += distance
        # return total_distance
        individual.fitness = total_distance
        return individual


class BasePopulationInitializer(abc.ABC):

    def __init__(self, population_size: int, mtsp_instance: MTSP, fitness_function_instance: BaseFitnessFunction):
        self.population_size: int = population_size
        self.mtsp_instance: MTSP = mtsp_instance
        self.fitness_function_instance: BaseFitnessFunction = fitness_function_instance

    @abc.abstractmethod
    def generate(self):
        pass


class RandomPopulationInitializer(BasePopulationInitializer):

    def __init__(self, population_size: int, mtsp_instance: MTSP, fitness_function_instance: BaseFitnessFunction):
        super().__init__(population_size=population_size, mtsp_instance=mtsp_instance, fitness_function_instance=fitness_function_instance)

    def generate(self) -> Population:
        individuals = [self._create_individual() for _ in range(self.population_size)]
        individuals = [self.fitness_function_instance.evaluate(individual) for individual in individuals]
        return Population(individuals=individuals)

    def _create_individual(self):
        route = list(range(1, self.mtsp_instance.num_cities))
        random.shuffle(route)
        partition_points = sorted(random.sample(route[:-1], self.mtsp_instance.num_salesmen - 1))
        individual = Individual(
            chromosome=[route[i:j] for i, j in zip([0] + partition_points, partition_points + [None])],
            generation=0,
        )
        return individual

class BaseGeneticAlgorithm(abc.ABC):

    def __init__(
        self,
        mtsp_instance: MTSP,
        num_generations: int,
        population_size: int,
        mutation_rate: float,
        population_initializer_class: BasePopulationInitializer,
        fitness_function_class: BaseFitnessFunction
        ):
        self.mtsp_instance = mtsp_instance
        self.num_generations: int = num_generations
        self.population_size: int = population_size
        self.mutation_rate: float = mutation_rate
        # Instantiate fitness function class
        self.fitness_function_instance = fitness_function_class(
            mtsp_instance=mtsp_instance,
        )
        # Instantiate solution initializer class
        self.population_initializer_instance = population_initializer_class(
            population_size=self.population_size,
            mtsp_instance=mtsp_instance,
            fitness_function_instance=self.fitness_function_instance,
        )
        # self.population: None | Population = None
        # self.solution_history: list = [] # TODO
        self._validate()

    def _validate(self):
        if self.num_generations < 1:
            raise ValueError(f"{self.num_generations}")
        if self.population_size < 1:
            raise ValueError(f"{self.population_size}")

    @abc.abstractmethod
    def _initialization(self):
        pass

    @abc.abstractmethod
    def _crossover_operator(self):
        pass

    @abc.abstractmethod
    def _mutation_operator(self):
        pass

    @abc.abstractmethod
    def _selection_operator(self):
        pass

    @abc.abstractmethod
    def run(self):
        pass


class GeneticAlgorithmOrderCrossOver(BaseGeneticAlgorithm):

    def __init__(self, mtsp_instance: MTSP, num_generations: int, population_size: int, mutation_rate: float, population_initializer_class: BasePopulationInitializer, fitness_function_class: BaseFitnessFunction):
        super().__init__(mtsp_instance, num_generations, population_size, mutation_rate, population_initializer_class, fitness_function_class)        
    
    def _initialization(self):
        return self.population_initializer_instance.generate()

    def _order_crossover(self, generation: int, parent1: Individual, parent2: Individual) -> Individual:
        # order crossover (OX)
        child = []

        p1_flattened = [city for route in parent1.chromosome for city in route]
        p2_flattened = [city for route in parent2.chromosome for city in route]

        start = random.randint(0, len(p1_flattened) - 1)
        end = random.randint(start, len(p1_flattened))

        child_route = p1_flattened[start:end]
        p2_remaining = [city for city in p2_flattened if city not in child_route]

        child_flattened = p2_remaining[:start] + child_route + p2_remaining[start:]

        partition_points = sorted(random.sample(range(1, len(child_flattened)), self.mtsp_instance.num_salesmen - 1))

        child = [child_flattened[i:j] for i, j in zip([0] + partition_points, partition_points + [None])]

        individual = Individual(chromosome=child, generation=generation)
        return individual

    # def _alternating_edges_crossover(self, generation: int, parent1: Individual, parent2: Individual) -> Individual:
    #     def build_alternating_edges_graph(parent1_edges, parent2_edges):
    #         graph = {}
    #         for edge in parent1_edges + parent2_edges:
    #             city1, city2 = edge
    #             if city1 not in graph:
    #                 graph[city1] = []
    #             if city2 not in graph:
    #                 graph[city2] = []
    #             graph[city1].append(city2)
    #             graph[city2].append(city1)
    #         return graph

    #     def traverse_alternating_edges_graph(start, graph):
    #         visited = set()
    #         stack = [start]
    #         path = []

    #         while stack:
    #             current = stack.pop()
    #             if current not in visited:
    #                 visited.add(current)
    #                 path.append(current)
    #                 for neighbor in graph[current]:
    #                     if neighbor not in visited:
    #                         stack.append(neighbor)
    #         return path

    #     p1_edges = [(route[i], route[i + 1]) for route in parent1.chromosome for i in range(len(route) - 1)]
    #     p2_edges = [(route[i], route[i + 1]) for route in parent2.chromosome for i in range(len(route) - 1)]

    #     graph = build_alternating_edges_graph(p1_edges, p2_edges)
    #     start = next(iter(graph))
    #     child_flattened = traverse_alternating_edges_graph(start, graph)

    #     # partition_points = sorted(random.sample(range(1, len(child_flattened)), self.mtsp_instance.num_salesmen - 1))

    #     # child = [child_flattened[i:j] for i, j in zip([0] + partition_points, partition_points + [None])]

    #     # individual = Individual(chromosome=child, generation=generation)
    #     # return individual
    #     # 
    #     print(child_flattened) 
    #     num_partition_points = self.mtsp_instance.num_salesmen - 1
    #     if num_partition_points >= len(child_flattened) or num_partition_points < 0:
    #         raise ValueError("Number of partition points is larger than or equal to the population size, or is negative.")

    #     partition_points = sorted(random.sample(range(1, len(child_flattened)), num_partition_points))

    #     child = [child_flattened[i:j] for i, j in zip([0] + partition_points, partition_points + [None])]

    #     individual = Individual(chromosome=child, generation=generation)
    #     return individual

    # def _alternating_edges_crossover(self, generation: int, parent1: Individual, parent2: Individual) -> Individual:
    #     child = []
    #     visited = set()

    #     p1_flattened = [city for route in parent1.chromosome for city in route]
    #     p2_flattened = [city for route in parent2.chromosome for city in route]

    #     for i in range(self.mtsp_instance.num_salesmen):
    #         if i % 2 == 0:
    #             current, other = p1_flattened, p2_flattened
    #         else:
    #             current, other = p2_flattened, p1_flattened

    #         start = random.randint(0, len(current) - self.mtsp_instance.num_salesmen)
    #         route = [current[start]]

    #         visited.add(current[start])

    #         # for _ in range(self.mtsp_instance.salesmen_lengths[i] - 1):
    #         for _ in range(self.mtsp_instance.salesmen_lengths[i] - 1):
    #             current_index = current.index(route[-1])
    #             neighbors = [current[(current_index + 1) % len(current)], current[(current_index - 1) % len(current)]]
    #             available_neighbors = [n for n in neighbors if n not in visited]

    #             if available_neighbors:
    #                 next_city = min(available_neighbors, key=lambda n: self.mtsp_instance._distance_matrix[route[-1]][n])
    #                 visited.add(next_city)
    #                 route.append(next_city)
    #             else:
    #                 next_city = min(set(current) - visited, key=lambda n: self.mtsp_instance._distance_matrix[route[-1]][n])
    #                 visited.add(next_city)
    #                 route.append(next_city)

    #         child.append(route)

    #         p1_flattened = [c for c in p1_flattened if c not in route]
    #         p2_flattened = [c for c in p2_flattened if c not in route]

    #     individual = Individual(chromosome=child, generation=generation)
    #     return individual

    # def _alternating_edges_crossover(self, generation: int, parent1: Individual, parent2: Individual) -> Individual:
    #         child = [[] for i in range(self.mtsp_instance.num_salesmen)]

    #         p1_flattened = [city for route in parent1.chromosome for city in route]
    #         p2_flattened = [city for route in parent2.chromosome for city in route]

    #         city_count = len(p1_flattened)
    #         edges = [(p1_flattened[i], p1_flattened[(i+1) % city_count], p2_flattened[i], p2_flattened[(i+1) % city_count]) for i in range(city_count)]

    #         for i in range(city_count):
    #             for j in range(self.mtsp_instance.num_salesmen):
    #                 if p1_flattened[i] in parent1.chromosome[j]:
    #                     route_idx = j
    #                     break
    #             if not child[route_idx]:
    #                 child[route_idx].append(p1_flattened[i])
    #             if (p1_flattened[i], p1_flattened[(i+1) % city_count], p2_flattened[i], p2_flattened[(i+1) % city_count]) in edges:
    #                 route_idx = (route_idx + 1) % self.mtsp_instance.num_salesmen
    #             child[route_idx].append(p1_flattened[(i+1) % city_count])

    #         individual = Individual(chromosome=child, generation=generation)
    #         return individual

    # def _alternating_edges_crossover(self, generation: int, parent1: Individual, parent2: Individual) -> Individual:
    #     def edges_from_chromosome(chromosome: List[List[int]]):
    #         edges = []
    #         for route in chromosome:
    #             for i in range(len(route)):
    #                 edges.append((route[i], route[(i + 1) % len(route)]))
    #         return edges

    #     def rebuild_chromosome(edges: List, num_salesmen: int) -> List[List[int]]:
    #         used_nodes = set()
    #         routes = []

    #         for _ in range(num_salesmen):
    #             route = []
    #             for edge in edges:
    #                 if edge[0] not in used_nodes and edge[1] not in used_nodes:
    #                     route.append(edge[0])
    #                     used_nodes.add(edge[0])
    #                     used_nodes.add(edge[1])
    #                     break

    #             current_node = route[-1]
    #             while current_node != route[0]:
    #                 for edge in edges:
    #                     if edge[0] == current_node and edge[1] not in used_nodes:
    #                         current_node = edge[1]
    #                         used_nodes.add(current_node)
    #                         route.append(current_node)
    #                         break
    #             routes.append(route)
    #         return routes

    #     p1_edges = edges_from_chromosome(parent1.chromosome)
    #     p2_edges = edges_from_chromosome(parent2.chromosome)

    #     child_edges = []
    #     for i in range(len(p1_edges)):
    #         if i % 2 == 0:
    #             child_edges.append(p1_edges[i])
    #         else:
    #             child_edges.append(p2_edges[i])

    #     child_chromosome = rebuild_chromosome(child_edges, self.mtsp_instance.num_salesmen)

    #     child = Individual(chromosome=child_chromosome, generation=generation)
    #     return child

    def _alternating_edges_crossover(self, generation: int, parent1: Individual, parent2: Individual) -> Individual:
        def edges_from_chromosome(chromosome: List[List[int]]):
            edges = []
            for route in chromosome:
                for i in range(len(route)):
                    edges.append((route[i], route[(i + 1) % len(route)]))
            return edges

        def rebuild_chromosome(edges: List, num_salesmen: int) -> List[List[int]]:
            used_nodes = set()
            routes = []

            for _ in range(num_salesmen):
                route = []
                for edge in edges:
                    if edge[0] not in used_nodes and edge[1] not in used_nodes:
                        route.append(edge[0])
                        used_nodes.add(edge[0])
                        used_nodes.add(edge[1])
                        break
                print("Used nodes  : ", used_nodes)

                current_node = route[-1] if route else None
                while current_node and current_node != route[0]:
                    for edge in edges:
                        if edge[0] == current_node and edge[1] not in used_nodes:
                            current_node = edge[1]
                            used_nodes.add(current_node)
                            route.append(current_node)
                            break
                    else:
                        current_node = None
                routes.append(route)
            return routes

        p1_edges = edges_from_chromosome(parent1.chromosome)
        p2_edges = edges_from_chromosome(parent2.chromosome)
        print(p2_edges)
        print(p1_edges)
        print()
        print()


        child_edges = []
        for i in range(len(p1_edges)):
            if i % 2 == 0:
                child_edges.append(p1_edges[i])
            else:
                child_edges.append(p2_edges[i])

        print("Child nodes : ", child_edges)

        child_chromosome = rebuild_chromosome(child_edges, self.mtsp_instance.num_salesmen)
        quit()

        child = Individual(chromosome=child_chromosome, generation=generation)
        return child
        
    def _edge_recombination_crossover(self, generation: int, parent1: Individual, parent2: Individual) -> Individual:
        # edge recombination crossover (ERX)

        # Combine the parent chromosomes into a single list of cities
        p1_flattened = [city for route in parent1.chromosome for city in route]
        p2_flattened = [city for route in parent2.chromosome for city in route]

        # TODO: There should be a better way to retrieve a list of all cities!
        all_cities = list(set(p1_flattened + p2_flattened))
        
        # Create the adjacency list for each city
        adjacency_lists = {}
        for city in all_cities:
            neighbors = set()
            if city in p1_flattened:
                idx = p1_flattened.index(city)
                if idx > 0:
                    neighbors.add(p1_flattened[idx-1])
                if idx < len(p1_flattened) - 1:
                    neighbors.add(p1_flattened[idx+1])
            if city in p2_flattened:
                idx = p2_flattened.index(city)
                if idx > 0:
                    neighbors.add(p2_flattened[idx-1])
                if idx < len(p2_flattened) - 1:
                    neighbors.add(p2_flattened[idx+1])
            adjacency_lists[city] = neighbors

        # Start with a random city and add it to the child chromosome
        child_chromosome = [random.choice(all_cities)]
        
        # Loop until all cities have been added to the child chromosome
        while len(child_chromosome) < len(all_cities):
            current_city = child_chromosome[-1]
            neighbors = adjacency_lists[current_city]
            
            # Remove current city from all neighbor lists
            for city, neighbor_list in adjacency_lists.items():
                if current_city in neighbor_list:
                    neighbor_list.remove(current_city)
            
            # Choose the neighbor with the fewest neighbors and add it to the child chromosome
            if len(neighbors) > 0:
                fewest_neighbors = min(neighbors, key=lambda x: len(adjacency_lists[x]))
            else:
                # If there are no unvisited neighboring cities, choose the next city randomly:
                # If the neighbors list is empty, it means that the current city does not have any
                # unvisited neighboring cities. This can happen if the two parents have disconnected
                # sub-tours, or if the algorithm has reached a dead-end in the graph of neighboring cities.
                unvisited_cities = set(all_cities) - set(child_chromosome)
                fewest_neighbors = random.choice(list(unvisited_cities))
            child_chromosome.append(fewest_neighbors)

            # Choose the neighbor with the fewest neighbors and add it to the child chromosome
            # fewest_neighbors = min(neighbors, key=lambda x: len(adjacency_lists[x]))
            # child_chromosome.append(fewest_neighbors)

        # Split the child chromosome into routes
        partition_points = sorted(random.sample(range(1, len(child_chromosome)), self.mtsp_instance.num_salesmen - 1))
        child = [child_chromosome[i:j] for i, j in zip([0] + partition_points, partition_points + [None])]
        
        individual = Individual(chromosome=child, generation=generation)
        return individual

    def _cycle_crossover(self, generation: int, parent1: Individual, parent2: Individual) -> Individual:
        # This implementation modifies the original _order_crossover function to implement the cycle crossover
        # (CX) operation. The main difference is in how the child's flattened chromosome is created. 
        # Instead of taking a random segment from one parent and filling in with the order from the other parent,
        # it constructs the child's flattened chromosome using alternating cycles from both parents.
        # The while loop iterates through the cycles in the parents' chromosomes and alternates between them to
        # create the child's flattened chromosome. The child's routes are then constructed by partitioning the
        # flattened chromosome using random partition points.
        child = []

        p1_flattened = [city for route in parent1.chromosome for city in route]
        p2_flattened = [city for route in parent2.chromosome for city in route]

        child_flattened = [None] * len(p1_flattened)
        start = 0
        remaining_indices = set(range(len(p1_flattened)))

        while remaining_indices:
            cycle_indices = [start]
            remaining_indices.remove(start)
            current = start

            while True:
                index_in_p2 = p2_flattened.index(p1_flattened[current])
                current = p1_flattened.index(p2_flattened[index_in_p2])

                if current == start:
                    break

                cycle_indices.append(current)
                remaining_indices.remove(current)

            for i in cycle_indices:
                child_flattened[i] = p1_flattened[i] if len(cycle_indices) % 2 == 1 else p2_flattened[i]

            if remaining_indices:
                start = min(remaining_indices)

        partition_points = sorted(random.sample(range(1, len(child_flattened)), self.mtsp_instance.num_salesmen - 1))

        child = [child_flattened[i:j] for i, j in zip([0] + partition_points, partition_points + [None])]

        individual = Individual(chromosome=child, generation=generation)
        return individual

    def _crossover_operator(self, generation: int, population: Population) -> Population:
        children_out = []
        while len(children_out) < self.population_size:
            parent1 = population.random_pick() 
            parent2 = population.random_pick()
            if parent1 != parent2:
                # child = self._order_crossover(generation, parent1, parent2)
                # child = self._edge_recombination_crossover(generation, parent1, parent2)
                # child = self._cycle_crossover(generation, parent1, parent2)
                child = self._alternating_edges_crossover(generation, parent1, parent2)
                children_out.append(child)
        return Population(individuals=children_out)

    def _mutation_operator(self, generation: int, population: Population) -> Population:
            children_out = []
            for i in range(len(population)):            
                routes = population[i].chromosome
                for route in routes:
                    for i in range(len(route)):
                        if random.random() < self.mutation_rate:
                            swap_index = random.randint(0, len(route) - 1)
                            route[i], route[swap_index] = route[swap_index], route[i]
                individual = Individual(chromosome=routes, generation=generation)
                children_out.append(individual)
            children_out = [self.fitness_function_instance.evaluate(child) for child in children_out]
            return Population(individuals=children_out)

    def _selection_operator(self, generation: int, parent_population: Population, child_population: Population):
        sorted_population = parent_population + child_population
        sorted_population.prune(population_size=self.population_size)
        return sorted_population

    def run(self):
        population = self._initialization()

        # Main loop
        for generation in range(self.num_generations):
            # Crossover Operation
            children = self._crossover_operator(generation, population)

            # Mutation Operation 
            children = self._mutation_operator(generation, children)

            # Selection
            population = self._selection_operator(generation, population, children)
            
            # Retrieve best individual
            best_individual = population.get_topk(k=1)

            print(f"Generation {generation + 1}: Best fitness  = {best_individual[0].fitness}")
            print(f"                           : Best solution = {best_individual[0].chromosome}")
            print()

if __name__ == "__main__":
    city_coordinates = [
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

    mtsp_instance = MTSP(city_coordinates=city_coordinates, num_salesmen=3, precompute_distances=True)
    ggoc = GeneticAlgorithmOrderCrossOver(
        mtsp_instance=mtsp_instance,
        num_generations=100,
        population_size=100,
        mutation_rate=0.1,
        population_initializer_class=RandomPopulationInitializer,
        fitness_function_class=FitnessFunctionMinimizeDistance,
    )

    final_solution = ggoc.run()





# # def create_individual_clustering(clusters, n_salesmen):
# #     # print(dir(clusters))
# #     # print(clusters.labels_)
# #     routes = [[] for _ in range(n_salesmen)]
# #     for i, cluster in enumerate(clusters):
# #         cluster_cities = [city_idx for city_idx, label in enumerate(cluster.labels_) if label == i]
# #         random.shuffle(cluster_cities)
# #         for j in range(n_salesmen):
# #             routes[j].extend(cluster_cities[j::n_salesmen])
# #     return routes
# def create_individual_clustering(labels, n_salesmen):
#     n_clusters = len(set(labels))
#     routes = [[] for _ in range(n_salesmen)]
#     for i in range(n_clusters):
#         cluster_cities = [city_idx + 1 for city_idx, label in enumerate(labels) if label == i]
#         random.shuffle(cluster_cities)
#         for j in range(n_salesmen):
#             routes[j].extend(cluster_cities[j::n_salesmen])
        
#     individual = Individual()
#     individual.solution = routes
#     return individual

# # def initial_population_kmeans(population_size, n_cities, n_salesmen, city_coords):
# #     clusters = KMeans(n_clusters=n_salesmen).fit(city_coords[1:]) # 1st coords is depot!
# #     population = [create_individual_clustering(clusters, n_salesmen) for _ in range(population_size)]
# #     return population

# def initial_population_kmeans(population_size, n_salesmen, city_coords):
#     kmeans = KMeans(n_clusters=n_salesmen).fit(city_coords[1:])
#     population = [create_individual_clustering(kmeans.labels_, n_salesmen) for _ in range(population_size)]
#     return population





# # Helper functions
# def create_individual():
#     route = list(range(1, n_cities))
#     random.shuffle(route)
#     partition_points = sorted(random.sample(route[:-1], n_salesmen - 1))
#     individual = Individual()
#     individual.solution = [route[i:j] for i, j in zip([0] + partition_points, partition_points + [None])]
#     return individual

# def fitness(individual):
#     total_distance = 0.0
#     for route in individual:
#         # print(route)
#         if len(route) == 0:
#             distance = numpy.inf
#         else:
#             distance = dist_matrix[0][route[0]] + dist_matrix[route[-1]][0]
#             for i in range(1, len(route)):
#                 distance += dist_matrix[route[i-1]][route[i]]
#         total_distance += distance
#     return total_distance

# def order_crossover(parent1, parent2):
#     child = []

#     p1_flattened = [city for route in parent1.solution for city in route]
#     p2_flattened = [city for route in parent2.solution for city in route]

#     start = random.randint(0, len(p1_flattened) - 1)
#     end = random.randint(start, len(p1_flattened))

#     child_route = p1_flattened[start:end]
#     p2_remaining = [city for city in p2_flattened if city not in child_route]

#     child_flattened = p2_remaining[:start] + child_route + p2_remaining[start:]

#     partition_points = sorted(random.sample(range(1, len(child_flattened)), n_salesmen - 1))

#     child = [child_flattened[i:j] for i, j in zip([0] + partition_points, partition_points + [None])]

#     individual = Individual()
#     individual.solution = child
#     # return child
#     return individual

# def mutate(individual, mutation_rate):
#     routes = individual.solution.copy()
#     for route in routes:
#         for i in range(len(route)):
#             if random.random() < mutation_rate:
#                 swap_index = random.randint(0, len(route) - 1)
#                 route[i], route[swap_index] = route[swap_index], route[i]
#     new_individual = Individual()
#     new_individual.solution = routes
#     new_individual.fitness = fitness(new_individual.solution) 
#     # return individual
#     return new_individual

# # def selection(population):
# #     # sorted_population = sorted(population, key=lambda x: fit_scores[x], reverse=True)
# #     # sorted_population = sorted(population, key=lambda x: x.fitness, reverse=True)
# #     sorted_population = sorted(population, key=lambda x: x.fitness, reverse=False)
# #     return sorted_population[:population_size]


# def selection(parent_population, child_population):
#     # sorted_population = sorted(parent_population + child_population, key=lambda x: x.fitness, reverse=False)
#     # elite = [min(parent_population, key=lambda x: x.fitness) if elitism else []]
#     # return elite + sorted_population[:population_size - len(elite)]

#     sorted_population = sorted(parent_population + child_population, key=lambda x: x.fitness, reverse=False)
#     # elite = [min(parent_population, key=lambda x: x.fitness) if elitism else []]
#     # return elite + 
#     return sorted_population[:population_size]


# def main():
#     # Initialize population

#     # - Random
#     population0 = [create_individual() for _ in range(population_size//2)]
#     # - Clustering
#     population1 = initial_population_kmeans(population_size//2, n_salesmen, cities)

#     population = population0 + population1 
#     print("Population size: ", len(population))

#     # Main loop
#     for gen in range(generations):
#         # Calculate the fitness of each individual in the population
#         for individual in population:
#             individual.fitness = fitness(individual.solution) 
       
#         # Crossover
#         children = []
#         while len(children) < population_size:
#             parent1 = random.choice(population)
#             parent2 = random.choice(population)
#             if parent1 != parent2:
#                 child = order_crossover(parent1, parent2)
#                 children.append(child)

#         # Mutation
#         for i in range(len(children)):
#             children[i] = mutate(children[i], mutation_rate)
        
#         # Selection
#         population = selection(population, children)
       
#         # Print best individual
#         best_individual = min(population, key=lambda x: x.fitness)

#         print(f"Generation {gen + 1}: Best fitness  = {fitness(best_individual.solution)}")
#         print(f"                    : Best solution = {best_individual.solution}")
#         print()
    
#     a = Individual()
#     a.solution = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
#     # a.solution = [[1], [2], [3], [4], [5], [6]]
#     print()
#     print(f"Known Best Fitness  = {fitness(a.solution)}")
#     print(f"Known Best Solution = {a.solution}")
#     print()





# if __name__ == "__main__":
#     main()
#     # population = initial_population_kmeans(population_size, n_cities, n_salesmen, cities)
#     # print(population)
#     # print(initial_population(population_size, n_cities, n_salesmen))
#     # plt.scatter([x[0] for x in cities], [x[1] for x in cities])
#     # plt.show()

