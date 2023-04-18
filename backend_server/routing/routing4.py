import logging
import abc
import pprint
import numpy
import random
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans

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

    def _crossover_operator(self, generation: int, population: Population) -> Population:
        children_out = []
        while len(children_out) < self.population_size:
            parent1 = population.random_pick() 
            parent2 = population.random_pick()
            if parent1 != parent2:
                child = self._order_crossover(generation, parent1, parent2)
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

