# Template-system final audit

Status: **PASS**

This follow-up keeps the EXP-0033 boundary precise: the complete hardened
product run is an Ubuntu acceptance result; the controlled Copier lifecycle and
new-executable mode checks run on both Ubuntu and macOS.

```text
component paths audited       274
infra wrapper targets         15
Python wrapper targets        166
immutable action pins         7
controlled new file mode      100755
fileMode=false control        100644
```

Validated:

* component source paths contain no final-template question syntax;
* a negative templated-path fixture is rejected;
* Vendir `includePaths`, `excludePaths`, `legalPaths: []` and no-`newRootPath`
  contracts are exact;
* all final-template wrapper targets exist and belong to declared components;
* product LICENSE output is explicitly selected while repository-root legal
  sentinels remain selection tests rather than implicit product files;
* workflows cited by the current template-system evidence use full action SHAs;
* pull-request matrix runs do not mint the write-capable lab App token;
* `core.fileMode=false` reproduces `100644`, while the controlled preflight
  records the new executable as `100755`;
* actual Python, Copier and uv versions match the documented exact contract.
