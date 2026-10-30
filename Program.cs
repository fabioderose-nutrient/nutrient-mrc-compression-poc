using GdPicture14;

// Usage: dotnet run -- [input.pdf] [--output DIR]
// Defaults: samples/color-scan-sample.pdf and ./output, relative to the current directory.
string input = Path.Combine("samples", "color-scan-sample.pdf");
string outputDir = "output";
for (int i = 0; i < args.Length; i++)
{
    if (args[i] is "--output" or "-o" && i + 1 < args.Length) outputDir = args[++i];
    else if (args[i] is "--help" or "-h")
    {
        Console.WriteLine("Usage: dotnet run -- [input.pdf] [--output DIR]");
        Console.WriteLine("  input.pdf     PDF to compress. Default: samples/color-scan-sample.pdf");
        Console.WriteLine("  --output DIR  Folder for the 10 output files. Default: output");
        return 0;
    }
    else input = args[i];
}
input = Path.GetFullPath(input);
outputDir = Path.GetFullPath(outputDir);
if (!File.Exists(input))
{
    Console.WriteLine($"Input file not found: {input}");
    return 1;
}
Directory.CreateDirectory(outputDir);

// License: the key comes from GDPICTURE_LICENSE_KEY. RegisterKEY must always be called:
// an empty key turns on evaluation mode (watermarked output). Without the call, the
// reducer returns InvalidLicense.
var licenseKey = (Environment.GetEnvironmentVariable("GDPICTURE_LICENSE_KEY") ?? "").Trim();
bool registered;
string reason = "RegisterKEY returned false";
try { registered = new LicenseManager().RegisterKEY(licenseKey); }
catch (Exception ex) { registered = false; reason = ex.Message; }
if (!registered && licenseKey.Length > 0)
{
    Console.WriteLine($"The license key was rejected ({reason}). Falling back to evaluation mode.\n");
    licenseKey = "";
    new LicenseManager().RegisterKEY("");
}
if (licenseKey.Length == 0)
    Console.WriteLine("No license key: running in evaluation mode (watermarked output).\n");

// Five MRC levels, from the best image quality (largest file) to the strongest compression.
var levels = new (string Name, PDFReducerImageQuality Quality)[]
{
    ("very-low-mrc", PDFReducerImageQuality.ImageQualityVeryVeryHigh),
    ("low-mrc", PDFReducerImageQuality.ImageQualityVeryHigh),
    ("medium-mrc", PDFReducerImageQuality.ImageQualityHigh),
    ("high-mrc", PDFReducerImageQuality.ImageQualityMedium),
    ("very-high-mrc", PDFReducerImageQuality.ImageQualityLow),
};

var inputSize = new FileInfo(input).Length;
Console.WriteLine($"Input: {Path.GetFileName(input)} ({FormatSize(inputSize)})");
Console.WriteLine();

var index = 0;
var written = 0;
// Each level is written twice: as a regular PDF, then linearized (Fast Web View).
foreach (var linearized in new[] { false, true })
{
    foreach (var (name, quality) in levels)
    {
        index++;
        var suffix = linearized ? "-linearized" : "";
        var output = Path.Combine(outputDir, $"{index:D2}-{name}{suffix}.pdf");

        var reducer = new GdPicturePDFReducer();
        var cfg = reducer.PDFReducerConfiguration;
        cfg.EnableMRC = true;
        cfg.ImageQuality = quality;
        cfg.DownscaleResolutionMRC = 150;
        cfg.DownscaleImages = true;
        cfg.DownscaleResolution = 150;
        cfg.PreserveSmoothing = true;
        cfg.EnableColorDetection = true;
        cfg.EnableJBIG2 = true;
        cfg.EnableCharRepair = true;
        cfg.PackDocument = true;
        cfg.PackFonts = true;
        cfg.RemoveMetadata = true;
        cfg.RemovePageThumbnails = true;
        cfg.RemovePagePieceInfo = true;
        cfg.RemoveLogicalStructure = true;
        cfg.RemoveJavaScript = true;
        cfg.RemoveEmbeddedFiles = true;
        cfg.OutputFormat = PDFReducerPDFVersion.PdfVersion17;
        cfg.FastWebView = linearized;

        var status = reducer.ProcessDocument(input, output);
        if (status != GdPictureStatus.OK)
        {
            Console.WriteLine($"{Path.GetFileName(output)}: FAILED ({status})");
            continue;
        }

        written++;
        var outputSize = new FileInfo(output).Length;
        var reduction = 100.0 * (1 - (double)outputSize / inputSize);
        var change = reduction >= 0 ? $"{reduction:F0}% smaller" : $"{-reduction:F0}% larger";
        Console.WriteLine($"{Path.GetFileName(output)}: {FormatSize(outputSize)} ({change})");
    }
}

Console.WriteLine();
Console.WriteLine($"Done. {written} files written to {outputDir}");
return written == index ? 0 : 1;

static string FormatSize(long bytes) =>
    bytes >= 1024 * 1024
        ? (bytes / 1048576.0).ToString("F1", System.Globalization.CultureInfo.InvariantCulture) + " MB"
        : (bytes / 1024.0).ToString("F0", System.Globalization.CultureInfo.InvariantCulture) + " KB";
