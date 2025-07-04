from deepdiff import DeepDiff


def compare_policies(local, aws):
    diff = DeepDiff(local, aws, ignore_order=True)
    return diff
