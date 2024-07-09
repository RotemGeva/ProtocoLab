using Serilog;
using System.Diagnostics;
using System.Runtime.CompilerServices;


namespace CompareCli;

/// <summary>
/// Manages the invocation of the compare cli.
/// </summary>
public static class CompareCliApi
{
    public record CompareRequest(string MrType, string RequirementsPath, string ActualDataPath);
    public record CompareResult();

    public class CliMgr
    {
        private static readonly ILogger _logger = Log.ForContext<CliMgr>();

        private string CompareDir => Path.Combine(Path.GetDirectoryName(System.Reflection.Assembly.GetEntryAssembly()!.Location)!, "cli");
        private string CompareDataDir => Path.Combine(CompareDir, "Data");

        private string CompareExePath => Path.Combine(CompareDir, "Compare.exe");

        private static void EmptyFolderExceptResults(DirectoryInfo directory)
        {
            DateTime timestamp = DateTime.Now;
            string formattedTimestamp = timestamp.ToString("ddMMyy_HHmmss");
            foreach (FileInfo file in directory.GetFiles())
            {
                if (file.Name.EndsWith("_Comparison.xlsx"))
                {
                    string newFileName = file.Name.Replace("Comparison.xlsx", "Comparison_" + formattedTimestamp + ".xlsx");
                    string newFilePath = Path.Combine(file.DirectoryName!, newFileName);
                    File.Move(file.FullName, newFilePath);
                }
                else if (!file.Name.Contains("_Comparison") && !file.Name.EndsWith("_Comparison"))
                    file.Delete();
            }
            foreach (DirectoryInfo subDirectory in directory.GetDirectories()) subDirectory.Delete(true);
        }

        public async Task<int> CompareAsync(CompareRequest request, CancellationToken ct = default)
        {
            void killProcesses(string name) => Array.ForEach(Process.GetProcessesByName(name), p => p.Kill());

            _logger.Debug("Comparing. The request: {@Request}", request);

            var resultDir = Path.Combine(CompareDataDir, request.MrType);

            if (Directory.Exists(resultDir))
            {
                EmptyFolderExceptResults(new DirectoryInfo(resultDir));
            }


                //if (Directory.Exists(resultDir))
                //   Directory.Delete(resultDir, true);

                // Directory.CreateDirectory(resultDir);

            var reqFileName = $"{request.MrType}_Requirements";
            reqFileName = Path.ChangeExtension(reqFileName, Path.GetExtension(request.RequirementsPath));
            var reqFilePath = Path.Combine(resultDir, reqFileName);

            File.Copy(request.RequirementsPath, reqFilePath);

            ProcessStartInfo startInfo = new()
            {
                FileName = CompareExePath,
                WorkingDirectory = Path.GetDirectoryName(CompareExePath),
                Arguments = $@"-r {"\"" + reqFilePath + "\""} -t {"\"" + request.ActualDataPath + "\""}",
                // Added double quotes to allow arguments with spaces
                CreateNoWindow = true
            };

            ProcessExtensions.StartProcessRequest startRequest = new(startInfo);

            startRequest.OnOutputLine += (line) => _logger.Debug(line);
            startRequest.OnErrorLine += (line) => _logger.Warning(line);

            _logger.Debug("Starting compare tool with request: {@Request}", startRequest);

            killProcesses("EXCEL");
            var exitCode = await startRequest.RunProcessAsync().ConfigureAwait(false);

            _logger.Debug("Compare tool done with code: {ExitCode}", exitCode);

            return exitCode;
        }

        public string GetResultsPath(CompareRequest request) =>
            Path.ChangeExtension(
                Path.Combine(CompareDataDir, request.MrType, $"{request.MrType}_Comparison"),
                Path.GetExtension(request.RequirementsPath));

        public string GetFolderPath(CompareRequest request) =>
                Path.Combine(CompareDataDir, request.MrType);
    }
}
