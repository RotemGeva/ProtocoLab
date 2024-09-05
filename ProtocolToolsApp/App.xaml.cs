using Serilog;
using Serilog.Events;
using System.IO;
using System.Windows;

namespace ProtocoLab;

/// <summary>
/// Interaction logic for App.xaml
/// </summary>
public partial class App : PrismApplication
{
    protected override Window CreateShell() => Container.Resolve<MainWindow>();

    protected override void RegisterTypes(IContainerRegistry containerRegistry)
    {
        // Initialize log folder
        string logsFolderPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "Logs");

        if (!Directory.Exists(logsFolderPath))
            Directory.CreateDirectory(logsFolderPath);

        /// NOTE!
        /// Logging must be initialized before any type registration that uses logging.
        LoggerConfiguration loggerConfiguration = new LoggerConfiguration()
        .Enrich.WithThreadId()
        .MinimumLevel.Is(LogEventLevel.Verbose);

        loggerConfiguration.WriteTo.File(
            path: "Logs/ProtocoLab.log",
            outputTemplate: "{Timestamp:yyyy-MM-dd HH:mm:ss.fff zzz} [{Level:u3}] ({SourceContext}) {Message:lj}{NewLine}{Exception}",
            rollingInterval: RollingInterval.Day,
            rollOnFileSizeLimit: true,
            retainedFileCountLimit: 16, shared: true);

        Log.Logger = loggerConfiguration.CreateLogger();

        var logger = Log.ForContext<App>();

        logger.Information("logging initialized");

        ViewModelLocationProvider.Register<MainWindow, MainWindowViewModel>();
        containerRegistry.RegisterDialog<NotificationDialog, NotificationDialogViewModel>();
        containerRegistry.RegisterDialog<YesNoDialog, YesNoDialogViewModel>();
    }

    protected override void OnInitialized()
    {
        //var regionManager = Container.Resolve<IRegionManager>();

        //regionManager?.RegisterViewWithRegion(nameof(MainWindow), CoreUiViewName.MainView);

        base.OnInitialized();
    }
}
