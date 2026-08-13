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
        ["nohup", "arka-plan", "background", "surec", "kopma", "daemon", "async"],
    ),
    (
        "disown -a",
        "disown",
        "Tüm arka plan işlerini mevcut terminal kabuğundan ayır / Disown background jobs from shell",
        ["disown", "jobs", "arka-plan", "ayir", "detach"],
    ),
    (
        "jobs -l",
        "jobs",
        "Mevcut kabukta çalışan arka plan işlerini ve PID numaralarını listele / List background jobs with PIDs",
        ["jobs", "arka-plan", "list", "pid", "surecler", "arkaplan"],
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
        "find . -type f -name '*.txt' -exec grep -H 'aranan' {} +",
        "find",
        "Belirli dosya türlerinde toplu arama yap / Find files and grep inside them",
        ["find", "exec", "grep", "toplu", "metin", "ara", "arama"],
    ),
    (
        "fd -e py",
        "fd",
        "Uzantıya göre hızlı dosya ara (fd-find) / Fast file search by extension using fd",
        ["fd", "find", "extension", "uzanti", "dosya", "ara", "bul"],
    ),
    (
        "grep -rnI 'aranan_metin' .",
        "grep",
        "İkili (binary) dosyaları atlayarak dizinde metin ara / Search text recursively skipping binary",
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
    (
        "ln -s <hedef_dosya> <link_adi>",
        "ln",
        "Sembolik bağlantı (Soft Symbolic Link) oluştur / Create symbolic soft link",
        ["ln", "link", "sembolik", "soft", "kisayol", "baglanti"],
    ),
    (
        "tree -L 2",
        "tree",
        "Dizin ağacını 2 seviye derinlikle görselleştir / Display directory tree up to depth 2",
        ["tree", "agac", "dizin", "gorsel", "yapi", "klasor"],
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
        "Satırları say, tekilleştir ve en çok tekrarlanana göre sırala / Count and sort unique occurrences",
        ["sort", "uniq", "say", "sirala", "tekil", "tekrar", "analiz"],
    ),
    (
        "wc -l <dosya.txt>",
        "wc",
        "Dosyadaki toplam satır sayısını say / Count total lines in file",
        ["wc", "satir", "say", "line", "count", "adet"],
    ),
    (
        "cut -d',' -f1,3 <veri.csv>",
        "cut",
        "CSV veya sınırlandırılmış metinden belirli alanları kes / Cut delimited columns",
        ["cut", "csv", "ayir", "kes", "kolon", "alan"],
    ),
    (
        "diff -u <dosya1> <dosya2>",
        "diff",
        "İki dosya arasındaki farkları birleşik (unified) formatta göster / Show unified diff between files",
        ["diff", "fark", "karsilastir", "dosyalar", "compare"],
    ),

    # --- Process Management & Killing ---
    (
        "ps aux | grep <isim>",
        "ps",
        "Çalışan süreçleri isme göre filtrele / Filter running processes by name",
        ["ps", "surec", "process", "filtre", "ara", "calisan", "grep"],
    ),
    (
        "pgrep -l <isim>",
        "pgrep",
        "İsme göre çalışan süreçlerin PID ve adlarını listele / List process IDs and names",
        ["pgrep", "pid", "surec", "bul", "process", "id"],
    ),
    (
        "kill -9 <PID>",
        "kill",
        "Belirtilen PID'ye zorla sonlandırma (SIGKILL) sinyali gönder / Force kill process by PID",
        ["kill", "oldur", "kapat", "sonlandir", "pid", "sigkill", "force"],
    ),
    (
        "pkill -9 -f <isim>",
        "pkill",
        "Komut satırında isim geçen tüm süreçleri zorla kapat / Force kill all processes matching name",
        ["pkill", "toplu", "kapat", "oldur", "sonlandir", "isim", "surec"],
    ),
    (
        "killall <uygulama>",
        "killall",
        "Belirtilen ada sahip tüm uygulamaları kapat / Kill all processes by application name",
        ["killall", "kapat", "surec", "uygulama", "hepsi"],
    ),
    (
        "lsof -i :<port>",
        "lsof",
        "Belirtilen portu kullanan süreci ve PID numarasını bul / Find process holding open port",
        ["lsof", "port", "pid", "hangi", "kullanan", "surec", "dinleyen"],
    ),
    (
        "fuser -k <port>/tcp",
        "fuser",
        "Belirtilen TCP portunu kilitleyen süreci doğrudan öldür / Kill process listening on TCP port",
        ["fuser", "port", "kill", "oldur", "kapat", "tcp"],
    ),
    (
        "top",
        "top",
        "Canlı sistem kaynakları ve süreç monitörü / Interactive real-time process monitor",
        ["top", "monitor", "cpu", "ram", "kaynak", "surecler"],
    ),
    (
        "htop",
        "htop",
        "Gelişmiş renkli ve interaktif süreç yöneticisi / Interactive colorful process viewer",
        ["htop", "monitor", "surec", "cpu", "ram", "yonetici"],
    ),

    # --- Disk & Memory Inspection ---
    (
        "df -h",
        "df",
        "Tüm disk bölümlerinin boş/dolu alan durumunu insan okunur göster / Show disk filesystem usage",
        ["df", "disk", "alan", "bos", "dolu", "gb", "hafiza", "storage"],
    ),
    (
        "du -sh * | sort -h",
        "du",
        "Mevcut klasördeki tüm dizinlerin boyutlarını hesapla ve sırala / Calculate directory disk usage",
        ["du", "boyut", "yer", "kaplayan", "klasor", "sirala", "disk"],
    ),
    (
        "ncdu",
        "ncdu",
        "Görsel interaktif disk kullanım analizörü / Interactive NCurses disk usage analyzer",
        ["ncdu", "disk", "analiz", "gorsel", "temizle", "yer"],
    ),
    (
        "free -h",
        "free",
        "RAM ve Swap bellek kullanımını insan okunur göster / Display free and used memory in human units",
        ["free", "ram", "bellek", "hafiza", "swap", "memory"],
    ),
    (
        "lsblk",
        "lsblk",
        "Tüm blok depolama cihazlarını ve bölümlerini listele / List block storage devices and partitions",
        ["lsblk", "disk", "bolum", "part", "depolama", "surucu"],
    ),

    # --- Systemd Services & Logs ---
    (
        "systemctl status <servis>",
        "systemctl",
        "Sistem servisinin çalışma durumunu göster / Show systemd service status",
        ["systemctl", "servis", "service", "durum", "status", "daemon"],
    ),
    (
        "sudo systemctl restart <servis>",
        "systemctl",
        "Sistem servisini yeniden başlat / Restart systemd service",
        ["systemctl", "restart", "yeniden", "baslat", "servis"],
    ),
    (
        "sudo systemctl enable --now <servis>",
        "systemctl",
        "Servisi açılışta otomatik başlayacak şekilde etkinleştir ve hemen başlat / Enable and start service",
        ["systemctl", "enable", "start", "acilis", "etkinlestir", "servis"],
    ),
    (
        "journalctl -u <servis> -f",
        "journalctl",
        "Sistem servisinin loglarını canlı olarak akışta izle / Follow systemd service logs live",
        ["journalctl", "log", "servis", "canli", "takip", "izle", "hata"],
    ),
    (
        "journalctl -xe",
        "journalctl",
        "En son sistem hatalarını ve açıklamalarını detaylı göster / View recent system error journals",
        ["journalctl", "hata", "error", "sistem", "log", "detay"],
    ),

    # --- Archives & Compression ---
    (
        "tar -czvf <arsiv.tar.gz> <dizin>/",
        "tar",
        "Dizini sıkıştırarak .tar.gz arşivi oluştur / Create compressed tar.gz archive",
        ["tar", "arsiv", "sikistir", "yedek", "paketle", "targz", "gzip"],
    ),
    (
        "tar -xzvf <arsiv.tar.gz>",
        "tar",
        ".tar.gz arşivini mevcut dizine aç / Extract tar.gz archive",
        ["tar", "ac", "cikar", "extract", "arsiv", "targz"],
    ),
    (
        "tar -tf <arsiv.tar.gz>",
        "tar",
        "Arşivi açmadan içindeki dosya listesini görüntüle / List contents of tar archive without extracting",
        ["tar", "list", "incele", "icerik", "dosyalar"],
    ),
    (
        "zip -r <arsiv.zip> <dizin>/",
        "zip",
        "Klasörü özyinelemeli olarak .zip arşivi yap / Create zip archive recursively",
        ["zip", "sikistir", "arsiv", "klasor", "paketle"],
    ),
    (
        "unzip <arsiv.zip>",
        "unzip",
        ".zip arşivini mevcut dizine çıkar / Extract zip archive",
        ["unzip", "ac", "cikar", "extract", "zip"],
    ),
    (
        "gzip -d <dosya.gz>",
        "gzip",
        ".gz sıkıştırılmış dosyasını aç / Decompress .gz file",
        ["gzip", "gunzip", "ac", "sikistirma", "decompress"],
    ),

    # --- Permissions, Users & Ownership ---
    (
        "chmod +x <script.sh>",
        "chmod",
        "Dosyaya çalıştırma yetkisi (executable) ver / Make file executable",
        ["chmod", "calistirma", "yetki", "executable", "script", "izin"],
    ),
    (
        "chmod 755 <dizin>/",
        "chmod",
        "Dizine standart rwxr-xr-x (755) izinlerini ata / Set standard directory permissions",
        ["chmod", "755", "izin", "yetki", "dizin", "klasor"],
    ),
    (
        "chmod 644 <dosya>",
        "chmod",
        "Dosyaya standart rw-r--r-- (644) izinlerini ata / Set standard file permissions",
        ["chmod", "644", "izin", "yetki", "dosya"],
    ),
    (
        "sudo chown -R $USER:$USER <dizin>/",
        "chown",
        "Dizinin ve altındaki tüm dosyaların sahipliğini mevcut kullanıcıya ata / Recursive chown to current user",
        ["chown", "sahip", "owner", "user", "kullanici", "yetki", "sahiplik"],
    ),
    (
        "sudo !!",
        "sudo",
        "Son çalıştırılan komutu sudo (root) yetkisiyle tekrar çalıştır / Rerun last command with sudo",
        ["sudo", "yetki", "root", "tekrar", "son"],
    ),
    (
        "whoami && id",
        "whoami",
        "Mevcut oturum açmış kullanıcıyı ve grup ID'lerini göster / Show current user and group memberships",
        ["whoami", "id", "kullanici", "user", "gruplar"],
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
        "curl ifconfig.me",
        "curl",
        "Dış dünyaya açık genel (Public) IP adresini sorgula / Query public external IP address",
        ["curl", "ip", "public", "dis-ip", "adres", "sorgula"],
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
    (
        "ping -c 4 <host>",
        "ping",
        "Hedef sunucuya 4 adet ICMP paketi göndererek erişilebilirliği test et / Test host reachability with ping",
        ["ping", "test", "erisim", "ag", "network", "gecikme", "latency"],
    ),

    # --- System Info, Environment & macOS ---
    (
        "uname -a",
        "uname",
        "İşletim sistemi çekirdek (Kernel) ve mimari bilgisini göster / Show OS kernel and architecture",
        ["uname", "kernel", "os", "surum", "mimari", "cekirdek"],
    ),
    (
        "uptime -p",
        "uptime",
        "Sistemin ne kadar süredir açık olduğunu göster / Show system uptime",
        ["uptime", "acik", "sure", "sistem", "calisma"],
    ),
    (
        "env | grep <degisken>",
        "env",
        "Ortam değişkenlerini (Environment variables) listele ve filtrele / Filter environment variables",
        ["env", "degisken", "ortam", "export", "path"],
    ),
    (
        "pbcopy < <dosya.txt>",
        "pbcopy",
        "Dosya içeriğini doğrudan panoya kopyala (macOS) / Copy file contents to clipboard",
        ["pbcopy", "pano", "kopyala", "clipboard", "macos", "copy"],
    ),
    (
        "pbpaste > <dosya.txt>",
        "pbpaste",
        "Panodaki metni dosyaya yapıştır (macOS) / Paste clipboard contents to file",
        ["pbpaste", "yapistir", "pano", "clipboard", "macos", "paste"],
    ),
    (
        "caffeinate -d",
        "caffeinate",
        "Terminal açıkken bilgisayarın uyku moduna geçmesini engelle (macOS) / Prevent display sleep",
        ["caffeinate", "uyku", "sleep", "engelle", "uyanik", "macos"],
    ),
    (
        "open .",
        "open",
        "Mevcut dizini macOS Finder veya varsayılan dosya yöneticisinde aç / Open current directory in Finder",
        ["open", "finder", "dizin", "klasor", "ac", "macos"],
    ),
]


class LinuxCommandsParser(BaseParser):
    """Parser & loader for essential Linux/Unix/macOS terminal recipes and cheat sheet."""

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
            tags.extend(["linux", "unix", "macos", "cli", "shell", "bash", "zsh", "terminal", "command", "komut", tool_category])
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
