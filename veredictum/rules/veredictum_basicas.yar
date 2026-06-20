/*
   Reglas YARA de arranque para Veredictum.
   Detección genérica de artefactos sospechosos en adjuntos de correo.
   Añade tus propias reglas en esta carpeta (*.yar / *.yara).
*/

rule ejecutable_windows_PE
{
    meta:
        description = "Ejecutable de Windows (PE). Sospechoso si el adjunto dice ser .zip/.pdf/.doc."
        autor = "Veredictum"
    condition:
        uint16(0) == 0x5A4D   // 'MZ'
}

rule office_macro_autoejecucion
{
    meta:
        description = "Documento ofimatico con macros de autoejecucion (AutoOpen/Document_Open)."
        autor = "Veredictum"
    strings:
        $a = "AutoOpen" ascii wide nocase
        $b = "Auto_Open" ascii wide nocase
        $c = "Document_Open" ascii wide nocase
        $d = "Workbook_Open" ascii wide nocase
    condition:
        any of them
}

rule powershell_sospechoso
{
    meta:
        description = "Indicios de descarga/ejecucion via PowerShell ofuscado."
        autor = "Veredictum"
    strings:
        $a = "powershell" ascii wide nocase
        $b = "-enc" ascii wide nocase
        $c = "DownloadString" ascii wide nocase
        $d = "IEX" ascii wide
        $e = "FromBase64String" ascii wide nocase
    condition:
        $a and any of ($b, $c, $d, $e)
}

rule descarga_o_shell
{
    meta:
        description = "Cadenas tipicas de descarga o ejecucion de comandos."
        autor = "Veredictum"
    strings:
        $a = "URLDownloadToFile" ascii wide nocase
        $b = "WScript.Shell" ascii wide nocase
        $c = "cmd.exe /c" ascii wide nocase
        $d = "Invoke-WebRequest" ascii wide nocase
    condition:
        any of them
}

rule eicar_test
{
    meta:
        description = "Fichero de prueba antivirus EICAR (no es malware real)."
        autor = "Veredictum"
    strings:
        $eicar = "X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
    condition:
        $eicar
}
