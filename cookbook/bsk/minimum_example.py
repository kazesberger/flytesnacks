# Copyright (C) 2015-2021 Blackshark.ai GmbH. All Rights reserved. www.blackshark.ai
from itertools import islice, chain
from typing import List, Iterable, Any, Generator

from flytekit import LaunchPlan, Resources, dynamic, task, workflow
from flytekit.core.node import Node
from flytekit.core.node_creation import create_node


def batch(iterable: Iterable[Any], batch_size: int) -> Generator[Iterable[Any], None, None]:
    """
    Generator that batches any iterable into chunks of the given size.
    The last chunk can have a smaller size.
    """
    orig_iter = iter(iterable)
    while True:
        try:
            batch_iter = islice(orig_iter, batch_size)
            yield chain([next(batch_iter)], batch_iter)
        except StopIteration:
            return


@task(requests=Resources(cpu="1", mem="1Gi"), limits=Resources(cpu="1", mem="1Gi"))
def create_input_integers_task(number_of_inputs: int) -> List[int]:
    return list(range(number_of_inputs))


@task(requests=Resources(cpu="1", mem="1Gi"), limits=Resources(cpu="1", mem="1Gi"))
def single_integer_dummy_task(some_integer: int) -> int:
    return some_integer


@task(requests=Resources(cpu="1", mem="1Gi"), limits=Resources(cpu="1", mem="1Gi"))
def three_integer_dummy_task(
    first_integer: int, second_integer: int, third_integer: int  # pylint: disable=unused-argument
) -> int:
    return first_integer


@workflow
def complex_single_integer_subworkflow(some_integer: int) -> None:
    integer_1 = single_integer_dummy_task(some_integer=some_integer)
    integer_2 = single_integer_dummy_task(some_integer=some_integer)
    integer_3 = single_integer_dummy_task(some_integer=some_integer)
    single_integer_dummy_task(some_integer=some_integer)
    single_integer_dummy_task(some_integer=some_integer)  # pylint: disable=unused-variable

    dependent_integer_1 = single_integer_dummy_task(some_integer=integer_1)
    dependent_integer_2 = single_integer_dummy_task(some_integer=dependent_integer_1)
    dependent_integer_3 = three_integer_dummy_task(
        first_integer=integer_1,
        second_integer=integer_2,
        third_integer=dependent_integer_2,
    )
    dependent_integer_4 = single_integer_dummy_task(some_integer=dependent_integer_3)

    three_integer_dummy_task(
        first_integer=some_integer,
        second_integer=dependent_integer_4,
        third_integer=dependent_integer_4,
    )

    three_integer_dummy_task(
        first_integer=some_integer,
        second_integer=integer_3,
        third_integer=integer_3,
    )


@dynamic
def dynamic_fan_out_task(input_integers: List[int]) -> None:
    for input_integer in input_integers:
        complex_single_integer_subworkflow(some_integer=input_integer)


@dynamic
def dynamic_fan_out_task_with_sequential_dependencies(input_integers: List[int]) -> None:
    nodes: List[Node] = []
    for input_integer in input_integers:
        new_node = create_node(complex_single_integer_subworkflow, some_integer=input_integer)
        if len(nodes) > 0:
            nodes[-1].runs_before(new_node)
        nodes.append(new_node)


@dynamic
def dynamic_fan_out_task_with_some_sequential_dependencies(input_integers: List[int]) -> None:
    last_nodes: List[Node] = []
    for input_batch in batch(input_integers, 10):
        new_nodes = [
            create_node(complex_single_integer_subworkflow, some_integer=input_integer) for input_integer in input_batch
        ]
        if len(last_nodes) > 0:
            for new_node in new_nodes:
                last_nodes[-1].runs_before(new_node)
        last_nodes.append(new_nodes[-1])


@workflow
def large_fan_out_fail(number_of_inputs: int) -> None:
    input_integers = create_input_integers_task(number_of_inputs=number_of_inputs)
    dynamic_fan_out_task(input_integers=input_integers)


@workflow
def large_fan_out_with_sequential_dependencies(number_of_inputs: int) -> None:
    input_integers = create_input_integers_task(number_of_inputs=number_of_inputs)
    dynamic_fan_out_task_with_sequential_dependencies(input_integers=input_integers)


@workflow
def large_fan_out_with_some_sequential_dependencies(number_of_inputs: int) -> None:
    input_integers = create_input_integers_task(number_of_inputs=number_of_inputs)
    dynamic_fan_out_task_with_some_sequential_dependencies(input_integers=input_integers)


LaunchPlan.create(
    "Minimum example with max parallelism",
    large_fan_out_fail,
    max_parallelism=100,
)
