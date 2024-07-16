using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace ProtocolsToolApp;

internal class CompareItem : BindableBase, IEquatable<CompareItem>
{
    private string? _mrType;
    private string? _reqPath;
    private string? _actualPath;

    public CompareItem()
    {
    }

    public CompareItem(string mrType, string reqPath, string actualPath)
    {
        _mrType = mrType;
        _reqPath = reqPath;
        _actualPath = actualPath;
    }

    /// <summary>
    /// Copy ctor
    /// </summary>
    public CompareItem(CompareItem other)
    {
        Copy(other);
    }

    public string? MrType
    {
        get => _mrType;
        set => SetProperty(ref _mrType, value);
    }

    public string? ReqPath
    {
        get => _reqPath;
        set => SetProperty(ref _reqPath, value);
    }

    public string? ActualPath
    {
        get => _actualPath;
        set => SetProperty(ref _actualPath, value);
    }

    public bool IsValid =>
        !string.IsNullOrWhiteSpace(MrType) &&
        !string.IsNullOrWhiteSpace(ReqPath) &&
        !string.IsNullOrWhiteSpace(ActualPath) &&
        File.Exists(ReqPath) &&
        File.Exists(ActualPath);


    /// <summary>
    /// We qualify 2 items as equal if their types (<see cref="MrType"/>) are equal.
    /// </summary>
    /// <param name="other"></param>
    /// <returns></returns>
    public bool Equals(CompareItem? other) =>
        other != null &&
        string.Equals(MrType, other.MrType, StringComparison.OrdinalIgnoreCase) &&
        string.Equals(ReqPath, other.ReqPath, StringComparison.OrdinalIgnoreCase) &&
        string.Equals(ActualPath, other.ActualPath, StringComparison.OrdinalIgnoreCase);

    public bool Identical(CompareItem? other) =>
        other != null &&
        string.Equals(MrType, other.MrType, StringComparison.OrdinalIgnoreCase);

    public void Copy(CompareItem from)
    {
        _mrType = from._mrType;
        _reqPath = from._reqPath;
        _actualPath = from._actualPath;

        RaisePropertyChanged(null); // all changed
    }
}
