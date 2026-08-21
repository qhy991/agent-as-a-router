Optimize Django's cascade-deletion collector so it selects only fields required
to discover downstream deletion relations. If pre-delete or post-delete signal
listeners need full model instances, preserve selection of all fields.

The named implementation module is `django/db/models/deletion.py`. Keep the
repair local to that implementation module. Do not modify tests, test models,
metadata, or dependencies.

The visible regression test is already present and fails on the seed:

`PYTHONPATH="$PWD" micromamba run -n acrouter-swe-django30-py38 python tests/runtests.py delete.tests.DeletionTests.test_only_referenced_fields_selected --verbosity 1`

Inspect the named implementation and nearest visible regression, implement the
smallest coherent repair, and use the visible failure details to correct an
incomplete edit before reporting the modified file and final verification.
