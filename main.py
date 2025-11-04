import argparse

from l_system.system_2d import System2D
from utils.fractal_logging import drawer_logger, l_system_logger
from utils.lsystem_loader import get_drawer, get_init_params


def main():
    parser = argparse.ArgumentParser(description="Draw Anything with LSystem")
    parser.add_argument("--object", help="object init", required=True)
    args = parser.parse_args()

    object_name = args.object

    print("Object name:", object_name)

    # Validate object supports coloring if requested
    drawer_class = get_drawer(
        object_name, templates_path="rule_templates/templates.json"
    )

    # Get initial parameters
    (
        init_rules,
        init_length,
        init_angle,
        init_width,
        init_iter,
        base_axiom,
    ) = get_init_params(object_name, templates_path="rule_templates/templates.json")
    drawer_class_instance = drawer_class(
        drawer_logger,
        base_width=init_width,
        base_length=init_length,
        base_angle=init_angle,
    )

    print(f"Loaded template for: {object_name}")
    print(f"Parameters: length={init_length}, angle={init_angle}, width={init_width}")
    print(f"Rules: {len(init_rules)}")

    l_system = System2D(axiom=base_axiom, logger=l_system_logger)
    l_system.add_rules(init_rules)

    state = l_system.generate(init_iter)

    drawer_class_instance.draw(sequence=state, save_file="fractal_0.png")


if __name__ == "__main__":
    main()
