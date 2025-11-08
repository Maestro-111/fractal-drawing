import argparse

from l_system.system_2d import System2D
from utils.fractal_logging import l_system_logger
from utils.lsystem_loader import Loader
from utils.rule_agent import RuleAgent


def main():
    parser = argparse.ArgumentParser(description="Draw Life with LSystem")
    parser.add_argument("--object", help="object init", required=True)

    args = parser.parse_args()

    object_name = args.object

    rule_agent = RuleAgent(logger=l_system_logger)
    init_loader = Loader(
        object_name,
        logger=l_system_logger,
        templates_path="rule_templates/templates.json",
    )

    object_template = init_loader.fetch_initial_template()

    prompt = rule_agent.generate_prompt(
        base_template=object_template, entity=object_name
    )
    modified_template = rule_agent.generate_random_object_with_openai(
        prompt, "rule_templates/agent_template.json"
    )

    drawer_class = init_loader.get_drawer(modified_template)

    (
        init_rules,
        init_length,
        init_angle,
        init_width,
        init_iter,
        base_axiom,
    ) = init_loader.get_init_params(modified_template)

    drawer_class_instance = drawer_class(
        l_system_logger,
        base_width=init_width,
        base_length=init_length,
        base_angle=init_angle,
    )

    l_system = System2D(axiom=base_axiom, logger=l_system_logger)
    l_system.add_rules(init_rules)

    state = l_system.generate(init_iter)

    drawer_class_instance.draw(sequence=state, save_file="fractal_0.png")


if __name__ == "__main__":
    main()
