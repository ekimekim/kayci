
KayCI is a Kubernetes-native CI system.
You define your pipelines as kubernetes objects, and KayCI acts as a controller to run them.

A **Pipeline** consists of a collection of kubernetes Jobs to run.
The jobs can be augmented with some extra metadata such as conditions or dependency info.

A **Trigger** details circumstances under which a **Pipeline** should be run.
An instance of a triggered pipeline, including any metadata given by the trigger, is known
as a **Run**.

Because the jobs specified in a pipeline can end up quite verbose and repetitive,
we highly recommend using some way to define them programmatically when creating your pipeline manifest,
for example using [jsonnet](https://jsonnet.org).

### Signifigant differences from typical CI systems

#### Pipeline is defined in cluster, not in code

While of course it is possible (and recommended) for you to store your pipeline manifests
in your codebase, KayCI will always follow the pipeline object that is defined in the kubernetes API,
not a local version from the codebase itself. This is important when running against untrusted codebases.
In typical CI systems that look for a file in the branch being run against, care must be taken
that an untrusted committer can't push a branch that tells CI to do nefarious things, or limits
the permissions that can be granted based on the source of the branch.

You should still consider what happens if your pipeline is run against a branch with arbitrary code
(for example, if you use a helper script to run things, that script may be controlled by an attacker),
but at the very least all user-controlled code will run inside a pod where (depending on the service
account you have given it) damage will hopefully be limited.

Of course, this setup may be harder to use as changes to the CI pipeline cannot be tested
without updating the CI pipeline. We suggest in these cases to manually apply a test pipeline
under a different name that is only triggered by your test branch.

#### Very limited feature set

KayCI is intended to be as thin a wrapper around kubernetes Jobs as is practical.
It's really more of an orchestrator for runnings Jobs, and those Jobs are then responsible
for other tasks that most CI systems would come with "out of the box". For example:
* Grabbing a local checkout of the branch being built. Your Job will need a script or similar to do this itself.
* Acquiring secrets. We suggest using kubernetes Secrets for this purpose and including them in your Jobs
  via a mount or environment variable.
