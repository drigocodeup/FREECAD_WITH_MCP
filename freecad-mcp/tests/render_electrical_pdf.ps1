param([Parameter(Mandatory=$true)][string]$InputPdf,
      [Parameter(Mandatory=$true)][string]$OutputPng,
      [switch]$Overwrite)
$ErrorActionPreference='Stop'
# Read-only PDF verification using the Windows PDF renderer, no extra package.
$Project=Split-Path $PSScriptRoot -Parent
$ModelsRoot=[IO.Path]::GetFullPath((Join-Path $Project '..\modelos')).TrimEnd('\')+'\'
$PdfPath=(Resolve-Path -LiteralPath $InputPdf).Path
$PngPath=[IO.Path]::GetFullPath($OutputPng)
if (!$PdfPath.StartsWith($ModelsRoot,[StringComparison]::OrdinalIgnoreCase) -or
    !$PngPath.StartsWith($ModelsRoot,[StringComparison]::OrdinalIgnoreCase)) { throw 'PDF e PNG devem estar em modelos.' }
if ([IO.Path]::GetExtension($PdfPath) -ine '.pdf' -or [IO.Path]::GetExtension($PngPath) -ine '.png') { throw 'Use entrada PDF e saida PNG.' }
if ((Test-Path -LiteralPath $PngPath) -and !$Overwrite) { throw 'PNG ja existe. Use outro nome ou -Overwrite.' }
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null=[Windows.Storage.StorageFile,Windows.Storage,ContentType=WindowsRuntime]
$null=[Windows.Data.Pdf.PdfDocument,Windows.Data.Pdf,ContentType=WindowsRuntime]
$null=[Windows.Storage.Streams.InMemoryRandomAccessStream,Windows.Storage.Streams,ContentType=WindowsRuntime]
$AwaitResult=([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.IsGenericMethod -and $_.GetGenericArguments().Count -eq 1 -and $_.GetParameters().Count -eq 1
} | Select-Object -First 1)
$AwaitAction=([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and !$_.IsGenericMethod -and $_.GetParameters().Count -eq 1
} | Select-Object -First 1)
function Wait-Result($AsyncOperation,[Type]$ResultType) {
    $Task=$AwaitResult.MakeGenericMethod($ResultType).Invoke($null,@($AsyncOperation))
    $Task.GetAwaiter().GetResult()
}
$PdfFile=Wait-Result ([Windows.Storage.StorageFile]::GetFileFromPathAsync($PdfPath)) ([Windows.Storage.StorageFile])
$Pdf=Wait-Result ([Windows.Data.Pdf.PdfDocument]::LoadFromFileAsync($PdfFile)) ([Windows.Data.Pdf.PdfDocument])
if ($Pdf.PageCount -ne 1) { throw 'Esperada uma pagina por prancha.' }
$Page=$Pdf.GetPage(0)
$PageWidth=$Page.Size.Width
$PageHeight=$Page.Size.Height
$Memory=New-Object Windows.Storage.Streams.InMemoryRandomAccessStream
$Options=New-Object Windows.Data.Pdf.PdfPageRenderOptions
$Options.DestinationWidth=[uint32](2400*$PageWidth/[Math]::Max($PageWidth,$PageHeight))
$RenderTask=$AwaitAction.Invoke($null,@($Page.RenderToStreamAsync($Memory,$Options)))
$null=$RenderTask.GetAwaiter().GetResult()
$ReadStream=[System.IO.WindowsRuntimeStreamExtensions]::AsStreamForRead($Memory.GetInputStreamAt(0))
[IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($PngPath)) | Out-Null
$Mode=if($Overwrite){[IO.FileMode]::Create}else{[IO.FileMode]::CreateNew}
$Output=[IO.File]::Open($PngPath,$Mode)
try { $ReadStream.CopyTo($Output) } finally { $Output.Dispose();$ReadStream.Dispose();$Memory.Dispose();$Page.Dispose() }
[pscustomobject]@{pdf=$PdfPath;page_count=$Pdf.PageCount;width_mm=$PageWidth*25.4/96;height_mm=$PageHeight*25.4/96;png=$PngPath} | ConvertTo-Json -Compress
