# import random
# from drawning.draw_2d import LSystemDrawer2D
# from l_system.system_2d import System2D

# class Evolution:
#
#     def __init__(self, population,  max_generation=5, elitism=3, size=10):
#
#         self.population = population
#         self.size = size
#         self.elitism = elitism
#         self.max_generation = max_generation
#
#
#     def run(self):
#
#         """
#
#         population example:
#
#             {
#                 "axioms":
#                     [
#                         ("A", f"F(1)[+({base_angle})A][-A]", 0.5),
#                         ("A", f"F(1)[+A][++({base_angle})A][-A]", 0.5),
#                     ],
#                 "rules":
#                     [
#                         ("F(x)", lambda x: f"F({x * 1.2})"),
#                     ]
#             }
#
#         """
#
#         population = self.population
#
#         for gen in range(self.max_generation):
#
#             scored = [((self.evaluate(rule), rule)]
#             best = sorted(scored, key=lambda x: x[0], reverse=True)[:self.elitism]
#             new_population = []
#
#             # keep the elite
#             for _, r, a in best:
#                 new_population.append((r, a))
#
#             # fill the rest with mutations/crossovers
#             while len(new_population) < self.size:
#                 parent = random.choice(best)
#                 child = self.mutate(parent[1], parent[2])
#                 new_population.append(child)
#
#             population = new_population
#
#         return population
#
#     def mutate(self, ruleset, angle):
#         pass
#
#     def crossover(self, ruleset1, ruleset2):
#         pass
#
#     def evaluate(self, ruleset, angle):
#
#         l_system = System2D()
