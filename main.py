import argparse

from l_system.system_2d import System2D
from utils.fractal_logging import l_system_logger
from utils.lsystem_loader import Loader
from utils.rule_agent import RuleAgent


def system_init(init_loader, template):
    drawer_class = init_loader.get_drawer(template)

    (
        init_rules,
        init_length,
        init_angle,
        init_width,
        init_iter,
        base_axiom,
    ) = init_loader.get_init_params(template)

    drawer_class_instance = drawer_class(
        l_system_logger,
        base_width=init_width,
        base_length=init_length,
        base_angle=init_angle,
    )

    l_system = System2D(axiom=base_axiom, logger=l_system_logger)
    l_system.add_rules(init_rules)

    return drawer_class_instance, l_system, init_iter


def main():
    parser = argparse.ArgumentParser(description="Draw Life with LSystem")

    parser.add_argument("--object", help="object init", required=True)
    parser.add_argument("--mode", help="how to run", required=True, type=int)

    args = parser.parse_args()

    object_name = args.object
    mode = args.mode

    if mode not in [0, 1, 2]:
        raise ValueError("Invalid mode")

    if mode == 0:
        l_system_logger.info("Default image generation mode")

        init_loader = Loader(
            object_name,
            logger=l_system_logger,
            templates_path="rule_templates/classic_templates.json",
        )

        object_template, _ = init_loader.fetch_initial_template()
        drawer_class_instance, l_system, init_iter = system_init(
            init_loader, object_template
        )

        token_state = l_system.generate(init_iter)
        drawer_class_instance.draw(tokens=token_state, save_file="fractal_0.png")

    elif mode == 1:
        l_system_logger.info("image generation mode with modifications")

        rule_agent = RuleAgent(logger=l_system_logger)

        init_loader = Loader(
            object_name,
            logger=l_system_logger,
            templates_path="rule_templates/generic_templates.json",
        )

        object_template, allowed_symbols = init_loader.fetch_initial_template()

        prompt = rule_agent.generate_prompt(
            base_template=object_template,
            entity=object_name,
            allowed_symbols=allowed_symbols,
        )

        modified_template = rule_agent.generate_random_object_with_openai(
            prompt, "rule_templates/agent_template.json"
        )

        drawer_class_instance, l_system, init_iter = system_init(
            init_loader, modified_template
        )

        token_state = l_system.generate(init_iter)
        drawer_class_instance.draw(tokens=token_state, save_file="fractal_0.png")

    else:
        l_system_logger.info("evolution based mage generation mode")


if __name__ == "__main__":
    main()
