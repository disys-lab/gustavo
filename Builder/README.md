To build python library package 

# Local Build :

e.g python builder.py git@repo


# Git Build : 

Git build commit message must have #git_build #buildpackage #version_tag

Version Tag #major or #minor or #patch which increments the version accordingly.

e.g. git commit -m "CL 71 Added support for Git build packgage name assigning automation #buildpackage #git_build #major"

Note: Not mentioning any build mode or git_build results just commiting the code to repo and doesn't trigger workflow.


# debugs

1. if any build failure occurs check the workflow and also make sure the secrets used in workflow are correct and still valid.
2. Make sure the builder.py has correct repo details to be cloned to start package build.
3. Please check commit history if needed as reference.
4. Also, make sure correct workflows branches are set to trigger actions.
