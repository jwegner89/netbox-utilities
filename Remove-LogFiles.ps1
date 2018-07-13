$TargetDate = (Get-Date).AddDays(-7)
$TargetFolder = "D:\logs"
$Files = Get-Childitem -Path $TargetFolder -Include "*.log" -Recurse | Where-Object {$_.LastWriteTime -le "$TargetDate"}
foreach ($File in $Files) {
    Remove-Item $File
}