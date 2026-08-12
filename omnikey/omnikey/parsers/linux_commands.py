"""Built-in Linux / Unix / macOS terminal commands & comprehensive cheat sheet recipes."""

from typing import List, Tuple

from omnikey.models import Keybinding
from omnikey.parsers.base import BaseParser
from omnikey.semantic.tagger import SemanticTagger


# Comprehensive curated Linux / Unix / macOS command recipes
LINUX_RECIPES: List[Tuple[str, str, str, List[str]]] = [
    # --- Background & Process Execution ---
    (
        "nohup <komut> > cikti.log 2>&1 &",
        "nohup",
        "Komutu terminal kapansa bile arka planda çalıştırmaya devam et / Run command immune to hangups",
        ["nohup", "arka-plan", "background", "surec", "kopma", "daemon"],
    ),
    (
        "disown -a",
        "disown",
        "Tüm arka plan işlerini mevcut terminal kabuğundan ayır / Disown background jobs from shell",
        ["disown", "jobs", "arka-plan", "ayir", "detach"],
    ),

    # --- File Finding & Search ---
    (
        "locate <dosya>",
        "locate",
        "Veritabanından hızlı dosya ara / Quick locate file in filesystem",
        ["locate", "find", "search", "dosya", "ara", "bul", "quick", "hizli"],
    ),
    (
        "find . -name '*.log'",
        "find",
        "Mevcut dizinde isim desenine göre dosya ara / Find files by name pattern",
        ["find", "name", "isim", "dosya", "ara", "bul", "uzanti", "search"],
    ),
    (
        "find . -type f -size +100M",
        "find",
        "100MB'dan büyük dosyaları bul / Find large files greater than 100MB",
        ["find", "size", "boyut", "buyuk", "large", "dosya", "yer", "disk", "mb", "gb"],
    ),
    (
        "find . -type f -mtime -7",
        "find",
        "Son 7 günde değiştirilen dosyaları bul / Find files modified in the last 7 days",
        ["find", "mtime", "tarih", "gecmis", "degisen", "modified", "recent", "son"],
    ),
    (
        "find . -name '*.tmp' -delete",
        "find",
        "Mevcut dizindeki tüm .tmp dosyalarını bularak sil / Find and delete temporary files",
        ["find", "delete", "sil", "temizle", "tmp", "dosya"],
    ),
    (
        "fd -e py",
        "fd",
        "Uzantıya göre hızlı dosya ara (fd-find) / Fast file search by extension using fd",
        ["fd", "find", "extension", "uzanti", "dosya", "ara", "bul"],
    ),
    (
        "grep -rn 'aranan_metin' .",
        "grep",
        "Dizin içindeki tüm dosyalarda metin ara / Recursively search text in files",
        ["grep", "metin", "ara", "bul", "search", "text", "string", "icerik"],
    ),
    (
        "rg -i 'aranan_metin'",
        "ripgrep",
        "Ripgrep ile çok hızlı metin ara (büyük/küçük harf duyarsız) / Fast case-insensitive search",
        ["rg", "ripgrep", "grep", "search", "metin", "ara", "hizli"],
    ),
    (
        "which <komut>",
        "which",
        "Komutun çalıştırılabilir ikili dosya yolunu göster / Locate executable binary in PATH",
        ["which", "nerede", "path", "binary", "komut", "yol"],
    ),

    # --- Text & Log Inspection ---
    (
        "tail -f <dosya.log>",
        "tail",
        "Log dosyasını canlı olarak anlık takip et / Follow log file in real-time",
        ["tail", "follow", "log", "canli", "takip", "izle", "son"],
    ),
    (
        "tail -n 100 <dosya.log>",
        "tail",
        "Dosyanın son 100 satırını ekrana yazdır / Output last 100 lines of file",
        ["tail", "satir", "son", "log", "line"],
    ),
    (
        "head -n 20 <dosya.txt>",
        "head",
        "Dosyanın ilk 20 satırını ekrana yazdır / Output first 20 lines of file",
        ["head", "satir", "ilk", "bas", "line"],
    ),
    (
        "less +F <dosya.log>",
        "less",
        "Canlı log izle ve Ctrl+C ile geçmişe kaydırma moduna geç / Follow log with scrollable buffer",
        ["less", "log", "canli", "scroll", "gecmis"],
    ),
    (
        "awk '{print $1, $3}' <dosya.txt>",
        "awk",
        "Metin tablosundan belirli sütunları filtrele ve yazdır / Print specific columns with awk",
        ["awk", "sutun", "kolon", "filtre", "metin", "column"],
    ),
    (
        "sed -i 's/eski/yeni/g' <dosya.txt>",
        "sed",
        "Dosya içindeki metni doğrudan bul ve değiştir (In-place) / Find and replace in-place with sed",
        ["sed", "degistir", "replace", "bul", "metin", "duzenle"],
    ),
    (
        "sort <dosya.txt> | uniq -c | sort -nr",
        "uniq",
        "Tekrarlayan satırları say ve en çoktan aza sırala / Count unique lines sorted by frequency",
        ["uniq", "sort", "tekrar", "sirala", "say", "count"],
    ),
    (
        "wc -l <dosya.txt>",
        "wc",
        "Dosyadaki toplam satır sayısını say / Count total lines in file",
        ["wc", "satir", "say", "count", "line"],
    ),
    (
        "jq '.' <veri.json>",
        "jq",
        "JSON çıktısını renklendir ve biçimlendir / Pretty-print and format JSON data",
        ["jq", "json", "format", "renk", "parse", "biçimlendir"],
    ),
    (
        "diff -u <dosya1> <dosya2>",
        "diff",
        "İki dosya arasındaki farkları Unified Diff olarak göster / Compare two files line by line",
        ["diff", "fark", "karsilastir", "compare"],
    ),

    # --- Processes, Ports & System ---
    (
        "lsof -i :8080",
        "lsof",
        "Belirtilen portu (8080) kullanan süreci ve PID'yi bul / Find process listening on port",
        ["lsof", "port", "pid", "process", "surec", "dinleyen", "portu", "bul", "net"],
    ),
    (
        "kill -9 $(lsof -t -i :8080)",
        "kill",
        "Portu kullanan süreci doğrudan öldür / Force kill process using specified port",
        ["kill", "port", "oldur", "öldür", "sonlandir", "sonlandır", "terminate", "lsof"],
    ),
    (
        "ps aux | grep <isim>",
        "ps",
        "Çalışan süreçleri filtrele / Filter running processes by name",
        ["ps", "process", "surec", "calisan", "grep", "list", "pid"],
    ),
    (
        "killall -9 <program_adi>",
        "killall",
        "Bir programın tüm açık süreçlerini zorla kapat / Kill all process instances by name",
        ["killall", "kill", "oldur", "kapat", "program", "surec"],
    ),
    (
        "pkill -f <kelime>",
        "pkill",
        "Komut satırında eşleşen tüm süreçleri öldür / Kill processes matching pattern",
        ["pkill", "kill", "surec", "oldur"],
    ),
    (
        "htop",
        "htop",
        "İnteraktif süreç ve sistem kaynak monitörü / Interactive system and CPU/RAM monitor",
        ["htop", "top", "cpu", "ram", "bellek", "kaynak", "monitor", "surec"],
    ),

    # --- Disk, Hardware & Storage ---
    (
        "du -sh * | sort -h",
        "du",
        "Mevcut dizindeki klasör boyutlarını sıralı göster / Show directory sizes sorted",
        ["du", "disk", "boyut", "size", "klasor", "yer", "kaplayan", "alan"],
    ),
    (
        "df -h",
        "df",
        "Disk bölümlerinin doluluk oranlarını göster / Check disk space and free capacity",
        ["df", "disk", "kapasite", "doluluk", "bos", "alan", "storage"],
    ),
    (
        "ncdu",
        "ncdu",
        "Görsel interaktif disk kullanım analizörü / Interactive NCurses disk usage analyzer",
        ["ncdu", "disk", "analiz", "temizle", "boyut", "large", "alan"],
    ),
    (
        "free -h",
        "free",
        "RAM ve Swap bellek kullanım durumunu göster / Display free and used memory in human units",
        ["free", "ram", "bellek", "memory", "swap", "alan"],
    ),
    (
        "uname -a",
        "uname",
        "İşletim sistemi çekirdek ve mimari bilgilerini göster / Print system information and kernel",
        ["uname", "os", "sistem", "kernel", "cekirdek", "surum"],
    ),

    # --- Service Management (systemd & macOS) ---
    (
        "systemctl status <servis>",
        "systemctl",
        "Sistem servisinin çalışma durumunu incele / Check systemd service status",
        ["systemctl", "servis", "service", "status", "durum", "systemd"],
    ),
    (
        "sudo systemctl restart <servis>",
        "systemctl",
        "Sistem servisini yeniden başlat / Restart systemd service",
        ["systemctl", "servis", "restart", "yeniden", "baslat"],
    ),
    (
        "journalctl -u <servis> -f -n 50",
        "journalctl",
        "Servise ait logları canlı olarak takip et / Follow service journal logs in real-time",
        ["journalctl", "log", "servis", "canli", "takip", "systemd"],
    ),
    (
        "brew services list",
        "brew",
        "macOS Homebrew servislerinin durumunu listele / List Homebrew background services",
        ["brew", "services", "servisler", "macos", "liste"],
    ),
    (
        "brew services restart <servis>",
        "brew",
        "macOS Homebrew servisini yeniden başlat / Restart Homebrew service",
        ["brew", "services", "restart", "yeniden", "baslat"],
    ),

    # --- Archives & Compression ---
    (
        "tar -czvf arsiv.tar.gz <dizin>",
        "tar",
        "Bir dizini tar.gz formatında sıkıştır / Compress directory into tar.gz archive",
        ["tar", "compress", "sikistir", "sıkıştır", "arsiv", "arşiv", "zip", "gz"],
    ),
    (
        "tar -xzvf arsiv.tar.gz",
        "tar",
        "tar.gz arşivini geçerli dizine aç / Extract tar.gz archive into current folder",
        ["tar", "extract", "ac", "aç", "cikar", "çıkar", "arsiv", "unzip"],
    ),
    (
        "tar -tvf arsiv.tar.gz",
        "tar",
        "Arşivi açmadan içindeki dosya listesini incele / List contents of tar.gz archive without extracting",
        ["tar", "list", "incele", "arsiv", "icerik"],
    ),
    (
        "unzip dosya.zip -d <hedef_dizin>",
        "unzip",
        "Zip dosyasını belirtilen hedef dizine aç / Extract zip archive to target directory",
        ["unzip", "zip", "ac", "aç", "cikar", "arsiv", "extract"],
    ),
    (
        "zip -r arsiv.zip <dizin>",
        "zip",
        "Dizini zip olarak sıkıştır / Create recursive zip archive",
        ["zip", "compress", "sikistir", "arsiv"],
    ),

    # --- Permissions & Ownership ---
    (
        "chmod +x <dosya>",
        "chmod",
        "Dosyaya çalıştırma yetkisi ver / Make file executable",
        ["chmod", "yetki", "izin", "execute", "calistir", "çalıştır", "permission"],
    ),
    (
        "chmod -R 755 <dizin>",
        "chmod",
        "Klasör ve alt dosyalarına standart okuma/yazma/çalıştırma izni ver / Set standard permissions",
        ["chmod", "izin", "permission", "755", "yetki"],
    ),
    (
        "chmod 600 ~/.ssh/id_rsa",
        "chmod",
        "SSH özel anahtarına sadece sahip erişim izni ver / Set secure SSH key permissions",
        ["chmod", "ssh", "600", "izin", "guvenlik"],
    ),
    (
        "chown -R $USER:$USER <dizin>",
        "chown",
        "Dizinin sahipliğini mevcut kullanıcıya ata / Change recursive ownership to current user",
        ["chown", "sahip", "owner", "user", "kullanici", "yetki"],
    ),
    (
        "sudo !!",
        "sudo",
        "Son çalıştırılan komutu sudo (root) yetkisiyle tekrar çalıştır / Rerun last command with sudo",
        ["sudo", "yetki", "root", "tekrar", "son"],
    ),

    # --- Network, Download & Transfer ---
    (
        "curl -sSL <url> | bash",
        "curl",
        "Web'den kurulum scripti indir ve çalıştır / Download and execute installer script",
        ["curl", "indir", "calistir", "kur", "install", "download", "web"],
    ),
    (
        "curl -I <url>",
        "curl",
        "Web sunucusunun HTTP başlık yanıtlarını (Headers) incele / Fetch HTTP response headers",
        ["curl", "http", "header", "baslik", "yanit", "status", "web"],
    ),
    (
        "curl -X POST -H 'Content-Type: application/json' -d '{\"k\":\"v\"}' <url>",
        "curl",
        "JSON gövdeli HTTP POST isteği gönder / Send HTTP POST request with JSON payload",
        ["curl", "post", "json", "api", "istek", "http"],
    ),
    (
        "wget -c <url>",
        "wget",
        "Yarıda kalan indirmeyi kaldığı yerden devam ettirerek indir / Resume broken file download",
        ["wget", "indir", "download", "devam", "dosya"],
    ),
    (
        "rsync -avzP <kaynak>/ <hedef>/",
        "rsync",
        "Dosyaları ilerleme çubuğuyla yerel/uzak hedefe senkronize et / Sync files with progress",
        ["rsync", "senkronize", "kopyala", "transfer", "sync", "backup", "yedek"],
    ),
    (
        "ssh -i ~/.ssh/key.pem user@host",
        "ssh",
        "Özel anahtar (PEM) dosyası belirterek SSH bağlan / Connect SSH with private key",
        ["ssh", "baglan", "uzak", "server", "sunucu", "key", "pem"],
    ),
    (
        "scp -P 22 -r <kaynak> user@host:<hedef>",
        "scp",
        "SSH üzerinden dosya/klasör kopyala / Secure copy over SSH",
        ["scp", "kopyala", "transfer", "ssh", "sunucu", "gonder"],
    ),
    (
        "ssh-copy-id -i ~/.ssh/id_rsa.pub user@host",
        "ssh-copy-id",
        "SSH açık anahtarını uzak sunucuya otomatik kopyala (Şifresiz giriş) / Copy SSH public key",
        ["ssh", "key", "sifresiz", "anahtar", "kopyala", "sunucu"],
    ),
    (
        "ss -tulpn",
        "ss",
        "Dinlenen tüm TCP/UDP portlarını ve ilişkili süreçleri listele / List listening network sockets",
        ["ss", "netstat", "port", "socket", "dinleyen", "ag", "network"],
    ),
    (
        "dig +short <alan_adi>",
        "dig",
        "Alan adının IP adresini hızlıca sorgula / Query DNS record quickly",
        ["dig", "dns", "ip", "sorgula", "domain", "alan-adi"],
    ),
    (
        "nc -zv <host> <port>",
        "nc",
        "Uzak sunucudaki portun açık olup olmadığını test et / Test if remote port is open",
        ["nc", "netcat", "port", "test", "kontrol", "ag", "open"],
    ),

    # --- Git Master Recipes ---
    (
        "git reset --soft HEAD~1",
        "git",
        "Son commit'i geri al fakat kod değişikliklerini koru (Staged) / Undo last commit keep changes",
        ["git", "commit", "geri", "al", "reset", "undo", "soft"],
    ),
    (
        "git reset --hard HEAD",
        "git",
        "Mevcut tüm stage edilmemiş ve yerel değişiklikleri sıfırla / Discard all local uncommitted changes",
        ["git", "reset", "hard", "sifirla", "geri-al", "temizle"],
    ),
    (
        "git stash && git stash pop",
        "git",
        "Değişiklikleri geçici olarak sakla ve geri yükle / Stash work in progress and restore",
        ["git", "stash", "sakla", "pop", "gecici", "kaydet"],
    ),
    (
        "git commit --amend --no-edit",
        "git",
        "Son commit mesajını değiştirmeden yeni stage edilen dosyaları son commit'e ekle / Amend last commit",
        ["git", "commit", "amend", "birlestir", "ekle", "guncelle"],
    ),
    (
        "git branch -D <dal_adi>",
        "git",
        "Birleştirilmemiş bir Git dalını zorla sil / Force delete branch",
        ["git", "branch", "dal", "sil", "delete", "remove"],
    ),
    (
        "git log --oneline --graph --all",
        "git",
        "Tüm dalların commit geçmişini görsel ağaç grafiğiyle göster / Pretty git log graph",
        ["git", "log", "graph", "agac", "gecmis", "dallar"],
    ),
    (
        "git diff --staged",
        "git",
        "Commit edilecek (stage edilmiş) değişiklikleri incele / View staged differences",
        ["git", "diff", "fark", "staged", "incele", "degisiklik"],
    ),
    (
        "git cherry-pick <commit_hash>",
        "git",
        "Başka daldaki belirli bir commit'i mevcut dala uygula / Apply specific commit to current branch",
        ["git", "cherry-pick", "commit", "uygula", "al"],
    ),
    (
        "git clean -fd",
        "git",
        "Git tarafından takip edilmeyen tüm sahipsiz dosya ve dizinleri sil / Clean untracked files",
        ["git", "clean", "temizle", "sil", "untracked"],
    ),
]


class LinuxCommandsParser(BaseParser):
    """Parser & loader for essential Linux/Unix terminal recipes and cheat sheet."""

    @property
    def tool_name(self) -> str:
        return "linux"

    def can_handle(self, file_path) -> bool:
        return False

    def parse(self, target_path) -> List[Keybinding]:
        return self.get_all_linux_commands()

    @classmethod
    def get_all_linux_commands(cls) -> List[Keybinding]:
        """Return structured keybinding/recipe objects for all Linux commands."""
        keybindings: List[Keybinding] = []
        for cmd, tool_category, desc, custom_tags in LINUX_RECIPES:
            tags = SemanticTagger.generate_tags(
                tool="linux",
                key_combo=cmd,
                action_raw=cmd,
                description=desc,
                mode="cli",
            )
            tags.extend(["linux", "cli", "shell", "bash", "zsh", "terminal", "command", "komut", tool_category])
            tags.extend(custom_tags)
            clean_tags = sorted(list(set(t.strip().lower() for t in tags if len(t.strip()) >= 2)))

            keybindings.append(
                Keybinding(
                    tool="linux",
                    key_combo=cmd,
                    action_raw=cmd,
                    description=desc,
                    source_file="builtin://linux_recipes",
                    mode="cli",
                    tags=clean_tags,
                )
            )
        return keybindings
