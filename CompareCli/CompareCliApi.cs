using Serilog;
using System.Diagnostics;


namespace CompareCli;

/// <summary>
/// Manages the invocation of the compare cli.
/// </summary>
public static class CompareCliApi
{
    public record CompareRequest(string MrType, string RequirementsPath, string ActualDataPath);
    public record CompareResult();

    public record MakeReqRequest(string DataPath, List<string> Protocols);
    public record MakeReqResult();
    public record ParseXMLRequest(string ActualDataPath);
    public record ParseXMLResult();

    public class CliMgr
    {
        private static readonly ILogger _logger = Log.ForContext<CliMgr>();

        private string ExternalToolDir => Path.Combine(Path.GetDirectoryName(System.Reflection.Assembly.GetEntryAssembly()!.Location)!, "cli");
        private string ExternalToolDataDir => Path.Combine(ExternalToolDir, "Data");

        private string ExternalToolExePath => Path.Combine(ExternalToolDir, "ExternalTool.exe");

        /// <summary>
        /// Handling parsing XML requests with external tool.
        /// </summary>
        /// <param name="request"></param>
        /// <param name="DataPath"></param>
        /// <param name="ct"></param>
        /// <returns></returns>
        public async Task<int> ParseXMLAsync(ParseXMLRequest request, string ActualDataPath, CancellationToken ct = default)
        {
            var resultDir = Path.Combine(ExternalToolDataDir, "temp");
            if (Directory.Exists(resultDir))
                Directory.Delete(resultDir, true);
            Directory.CreateDirectory(resultDir);
            _logger.Debug("Parsing XML. The request: {@Request}", request);
            ProcessStartInfo startInfo = new()
            {
                FileName = ExternalToolExePath,
                WorkingDirectory = Path.GetDirectoryName(ExternalToolExePath),
                Arguments = $@"-a {"\"" + request.ActualDataPath + "\""} -f x",
                // Added double quotes to allow arguments with spaces
                CreateNoWindow = true
            };

            ProcessExtensions.StartProcessRequest startRequest = new(startInfo);

            startRequest.OnOutputLine += (line) => _logger.Debug(line);
            startRequest.OnErrorLine += (line) => _logger.Warning(line);

            _logger.Debug("Starting external tool with request: {@Request}", startRequest);

            var exitCode = await startRequest.RunProcessAsync().ConfigureAwait(false);

            _logger.Debug("External tool done with code: {ExitCode}", exitCode);

            return exitCode;
        }

        /// <summary>
        /// Handeling making requirements requests with external tool.
        /// </summary>
        /// <param name="request"></param>
        /// <param name="protocols">Protocols to preserve in requirements file.</param>
        /// <param name="ct"></param>
        /// <returns></returns>
        public async Task<int> MakeReqAsync(MakeReqRequest request, List<string> protocols, CancellationToken ct = default)
        {
            var resultDir = Path.Combine(ExternalToolDataDir, "Requirements");
            Directory.CreateDirectory(resultDir);
            var a = protocols.ToArray();
            _logger.Debug("Making requirements. The request: {@Request}", request);
            ProcessStartInfo startInfo = new()
            {
                FileName = ExternalToolExePath,
                WorkingDirectory = Path.GetDirectoryName(ExternalToolExePath),
                Arguments = $@"-a {"\"" + request.DataPath + "\""} -p {protocols.Aggregate((x, y) => $"{x} {y}")} -f r",
                // Added double quotes to allow arguments with spaces
                CreateNoWindow = true
            };

            ProcessExtensions.StartProcessRequest startRequest = new(startInfo);

            startRequest.OnOutputLine += (line) => _logger.Debug(line);
            startRequest.OnErrorLine += (line) => _logger.Warning(line);

            _logger.Debug("Starting external tool with request: {@Request}", startRequest);

            killProcesses("EXCEL");
            var exitCode = await startRequest.RunProcessAsync().ConfigureAwait(false);
            killProcesses("EXCEL");

            _logger.Debug("External tool done with code: {ExitCode}", exitCode);

            return exitCode;
        }

        /// <summary>
        /// Handleing comapre requests with external tool.
        /// </summary>
        /// <param name="request"></param>
        /// <param name="ct"></param>
        /// <returns></returns>
        public async Task<int> CompareAsync(CompareRequest request, CancellationToken ct = default)
        {

            _logger.Debug("Comparing... The request: {@Request}", request);

            var resultDir = Path.Combine(ExternalToolDataDir, request.MrType);

            if (Directory.Exists(resultDir))
                EmptyFolderExceptResults(new DirectoryInfo(resultDir));
            else
            {
                _logger.Information($"{resultDir} does not exist. Creating new folder...");
                Directory.CreateDirectory(resultDir);
            }

            var reqFileName = $"{request.MrType}_Requirements.xlsx";
            var reqFilePath = Path.Combine(resultDir, reqFileName);

            File.Copy(request.RequirementsPath, reqFilePath);

            ProcessStartInfo startInfo = new()
            {
                FileName = ExternalToolExePath,
                WorkingDirectory = Path.GetDirectoryName(ExternalToolExePath),
                Arguments = $@"-r {"\"" + reqFilePath + "\""} -a {"\"" + request.ActualDataPath + "\""} -f c",
                // Added double quotes to allow arguments with spaces
                CreateNoWindow = true
            };

            ProcessExtensions.StartProcessRequest startRequest = new(startInfo);

            startRequest.OnOutputLine += (line) => _logger.Debug(line);
            startRequest.OnErrorLine += (line) => _logger.Warning(line);

            _logger.Debug("Starting external tool with request: {@Request}", startRequest);

            killProcesses("EXCEL");
            var exitCode = await startRequest.RunProcessAsync().ConfigureAwait(false);
            killProcesses("EXCEL");
            _logger.Debug("External tool done with code: {ExitCode}", exitCode);

            return exitCode;
        }

        public string GetResultsPath(CompareRequest request) =>
                Path.Combine(ExternalToolDataDir, request.MrType, $"{request.MrType}_Comparison.xlsx");

        public string GetFolderPath(CompareRequest request) =>
                Path.Combine(ExternalToolDataDir, request.MrType);

        /// <summary>
        /// Preserving previous comparison results in target folder.
        /// </summary>
        /// <param name="directory">Target directory to preseve its results.</param>
        private static void EmptyFolderExceptResults(DirectoryInfo directory)
        {
            _logger.Information($"Preparing target directory: {directory}.");
            DateTime timestamp = DateTime.Now;
            string formattedTimestamp = timestamp.ToString("ddMMyy_HHmmss");
            foreach (FileInfo file in directory.GetFiles())
            {
                if (file.Name.EndsWith("_Comparison.xlsx")) //Keeping previous results in folder.
                {
                    _logger.Information($"Adding timstamp to file: {file}...");
                    string newFileName = file.Name.Replace("Comparison.xlsx", "Comparison_" + formattedTimestamp + ".xlsx");
                    string newFilePath = Path.Combine(file.DirectoryName!, newFileName);
                    File.Move(file.FullName, newFilePath);
                }
                else if (!file.Name.Contains("_Comparison") && !file.Name.EndsWith("_Comparison"))
                {
                    _logger.Information($"{file} is not previous comparison results. Deleting file...");
                    file.Delete();
                }
            }
            foreach (DirectoryInfo subDirectory in directory.GetDirectories()) subDirectory.Delete(true);
        }

        private void killProcesses(string name) => Array.ForEach(Process.GetProcessesByName(name), p => p.Kill());
    }

}
