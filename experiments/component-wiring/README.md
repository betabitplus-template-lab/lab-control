# Component wiring decision

A component gitlink update changes only sources already wired by the final template. A new component file does **not** implicitly create an output path; adding or renaming output paths is an intentional template change reviewed in that template repository.

`WIRING.json` is not required at runtime or for release. The filesystem, gitlink and generic checks are authoritative. Remove the committed manifest; when an ownership report is useful, generate it deterministically as a CI artifact from tracked symlinks and executable wrappers.

A deleted or renamed component target leaves a broken symlink and fails `find -L`. The negative PR must remain unmerged.
