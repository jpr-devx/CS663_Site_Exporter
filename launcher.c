/*
 * CS631-Site-Exporter launcher
 * Compiles to a named binary so macOS Background Activities shows a readable
 * name instead of "bash". Resolves run.sh relative to this binary's location.
 */
#include <mach-o/dyld.h>
#include <stdio.h>
#include <string.h>
#include <sys/wait.h>
#include <unistd.h>

int main(void) {
    char exe[1024];
    uint32_t size = sizeof(exe);
    if (_NSGetExecutablePath(exe, &size) != 0) {
        fprintf(stderr, "CS631-Site-Exporter: could not resolve executable path\n");
        return 1;
    }

    /* Trim the binary name to get its directory */
    char *slash = strrchr(exe, '/');
    if (!slash) return 1;
    *slash = '\0';

    /* Build path to run.sh in the same directory */
    char script[1024];
    if (snprintf(script, sizeof(script), "%s/run.sh", exe) >= (int)sizeof(script)) {
        fprintf(stderr, "CS631-Site-Exporter: path too long\n");
        return 1;
    }

    char *const args[] = { "/bin/bash", script, NULL };

    pid_t pid = fork();
    if (pid < 0) {
        perror("CS631-Site-Exporter: fork failed");
        return 1;
    }
    if (pid == 0) {
        /* Child: replace with bash */
        execv("/bin/bash", args);
        perror("CS631-Site-Exporter: execv failed");
        _exit(1);
    }

    /* Parent: wait for bash to finish and propagate its exit code */
    int status;
    waitpid(pid, &status, 0);
    return WIFEXITED(status) ? WEXITSTATUS(status) : 1;
}
