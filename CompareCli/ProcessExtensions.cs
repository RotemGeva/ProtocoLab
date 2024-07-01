using Serilog;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace CompareCli;

internal static class ProcessExtensions
{
    private static ILogger _logger = Log.ForContext("SourceContext", nameof(ProcessExtensions));

    public delegate void ProcessOutputDelegate(string line);

    public class StartProcessRequest
    {
        public ProcessStartInfo StartInfo { get; }
        public ProcessOutputDelegate? OnOutputLine { get; set; }
        public ProcessOutputDelegate? OnErrorLine { get; set; }

        public StartProcessRequest(ProcessStartInfo startInfo)
        {
            StartInfo = startInfo;
        }
    }

    public static async Task<int> RunProcessAsync(this StartProcessRequest request, CancellationToken ct = default)
    {
        _logger.Information("Running process {Name} {Arguments}", request.StartInfo.FileName, request.StartInfo.Arguments);

        // List of tasks to wait for a whole process exit
        LinkedList<Task> processTasks = new();

        using (Process process = new() { StartInfo = request.StartInfo })
        {
            if (request.OnOutputLine != null)
            {
                process.StartInfo.RedirectStandardOutput = true;

                var stdOutCloseEvent = new TaskCompletionSource<bool>();

                process.OutputDataReceived += (s, e) =>
                {
                    if (e.Data == null)
                    {
                        stdOutCloseEvent.TrySetResult(true);
                    }
                    else
                    {
                        _logger.Verbose("stdout: {Output}", e.Data);
                        request.OnOutputLine(e.Data);
                    }
                };

                processTasks.AddLast(stdOutCloseEvent.Task);
            }
            else
            {
                process.StartInfo.RedirectStandardOutput = false;
            }

            if (request.OnErrorLine != null)
            {
                process.StartInfo.RedirectStandardError = true;

                var stdErrCloseEvent = new TaskCompletionSource<bool>();

                process.ErrorDataReceived += (s, e) =>
                {
                    if (e.Data == null)
                    {
                        stdErrCloseEvent.TrySetResult(true);
                    }
                    else
                    {
                        request.OnErrorLine(e.Data);
                        _logger.Verbose("stderr: {Error}", e.Data);
                    }
                };

                processTasks.AddLast(stdErrCloseEvent.Task);
            }
            else
            {
                process.StartInfo.RedirectStandardError = false;
            }

            if (!process.Start())
            {
                _logger.Warning("{Name} {Arguments} not started. Exit code: {ExitCode}", request.StartInfo.FileName, request.StartInfo.Arguments, process.ExitCode);
                return process.ExitCode;
            }

            // Reads the output stream first as needed and then waits because deadlocks are possible
            if (process.StartInfo.RedirectStandardOutput)
                process.BeginOutputReadLine();
            if (process.StartInfo.RedirectStandardError)
                process.BeginErrorReadLine();

            var waitForExit = process.WaitForExitAsync(ct);

            processTasks.AddLast(waitForExit);

            try
            {
                await Task.WhenAll(processTasks).ConfigureAwait(false);
            }
            catch (Exception ex)
            {
                _logger.Error(ex, "Failed to run {Name} {Arguments}", request.StartInfo.FileName, request.StartInfo.Arguments);

                try
                {
                    process.Kill();
                }
                catch (Exception killex)
                {
                    _logger.Error(killex, "Failed to kill {Name} {Arguments}", request.StartInfo.FileName, request.StartInfo.Arguments);
                }

                throw;
            }

            _logger.Information("{Name} {Arguments} returned with exit code: {ExitCode}", request.StartInfo.FileName, request.StartInfo.Arguments, process.ExitCode);

            return process.ExitCode;
        }
    }
}
