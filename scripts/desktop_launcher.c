/* Finder entrypoint: bundled Python, bundled sources, no repository/venv lookup. */
#include <mach-o/dyld.h>
#include <libgen.h>
#include <limits.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

int main(int argc, char **argv) {
    char exe[PATH_MAX], resolved[PATH_MAX], root[PATH_MAX], python[PATH_MAX];
    char entry[PATH_MAX], profile[PATH_MAX], home[PATH_MAX], certificates[PATH_MAX];
    uint32_t size = sizeof exe;
    if (_NSGetExecutablePath(exe, &size) || !realpath(exe, resolved)) return 1;
    snprintf(root, sizeof root, "%s/../Resources/app", dirname(resolved));
    snprintf(python, sizeof python, "%s/.runtime-python/bin/python3.11", root);
    snprintf(home, sizeof home, "%s/.runtime-python", root);
    snprintf(entry, sizeof entry, "%s/scripts/desktop_entry.py", root);
    snprintf(profile, sizeof profile, "%s/desktop-profile.json", root);
    snprintf(certificates, sizeof certificates, "%s/.runtime-python/certs/system-roots.pem", root);
    unsetenv("PYTHONPATH"); unsetenv("PYTHONSTARTUP"); unsetenv("PYTHONINSPECT");
    unsetenv("PYTHONUSERBASE"); unsetenv("DYLD_LIBRARY_PATH");
    setenv("PYTHONHOME", home, 1);
    setenv("PYTHONNOUSERSITE", "1", 1);
    setenv("PYTHONDONTWRITEBYTECODE", "1", 1);
    setenv("SSL_CERT_FILE", certificates, 1);
    char **args = calloc((size_t)argc + 6, sizeof *args);
    if (!args) return 1;
    args[0] = python; args[1] = "-s"; args[2] = "-B"; args[3] = entry;
    args[4] = "--profile"; args[5] = profile;
    for (int i = 1; i < argc; ++i) args[i + 5] = argv[i];
    execv(python, args);
    perror("COSMOS embedded runtime could not start");
    return 1;
}
