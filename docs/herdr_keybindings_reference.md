# 📋 Herdr Tam Kısayol (Hotkey) ve Özellikler Referans Kataloğu

Bu belge, **Herdr** terminal çalışma alanı yöneticisinde kullanabileceğiniz tüm geçerli eylemleri, varsayılan tuş atamalarını, modal navigasyon modlarını ve özel pop-up komutlarını içerir.

---

## ⚙️ Yapılandırma Dosyası Konumu
* **Yol:** `~/.config/herdr/config.toml`
* **Yapılandırma Bölümü:** `[keys]`

---

## 1. 🎛️ Genel Sistem ve Ön-Ek (Prefix) Ayarları

| Eylem (Action) | Varsayılan | Açıklama |
| :--- | :--- | :--- |
| `prefix` | `"ctrl+b"` | Prefix moduna giriş tuşu (Örn: `"ctrl+s"`, `"f12"`, `"-"`) |
| `help` | `"prefix+?"` | Herdr yardım ve kısayol menüsünü açar |
| `settings` | `"prefix+s"` | Ayarlar arayüzünü açar |
| `detach` | `"prefix+q"` | Persistent oturumdan ayrılır (server arka planda çalışmaya devam eder) |
| `reload_config` | `"prefix+shift+r"` | `config.toml` dosyasını yeniden yükler |
| `toggle_sidebar` | `"prefix+b"` | Yan çubuğu (Sidebar) açar veya gizler |
| `remote_image_paste` | `"ctrl+v"` | `herdr --remote` oturumunda pano resmini yapıştırır |

---

## 2. 🗂️ Çalışma Alanı (Workspace) Navigasyonu

| Eylem (Action) | Varsayılan | Önerilen / Tmux Uyumlu | Açıklama |
| :--- | :--- | :--- | :--- |
| `workspace_picker` | `"prefix+w"` | `"prefix+w"` | Tüm çalışma alanlarını gösteren seçici |
| `goto` | `"prefix+g"` | `"prefix+g"` | Hızlı atlama ve arama menüsü |
| `new_workspace` | `"prefix+shift+n"` | `"prefix+shift+n"` | Yeni bir bağımsız çalışma alanı açar |
| `rename_workspace` | `"prefix+shift+w"` | `"prefix+shift+w"` | Mevcut çalışma alanını yeniden adlandırır |
| `close_workspace` | `"prefix+shift+d"` | `"prefix+shift+d"` | Mevcut çalışma alanını kapatır |
| `previous_workspace` | *(tanımsız)* | `"prefix+p"` | Önceki çalışma alanına geçer |
| `next_workspace` | *(tanımsız)* | `"prefix+n"` | Sonraki çalışma alanına geçer |
| `switch_workspace` | *(tanımsız)* | `"prefix+1..9"` | İndeks numarasına göre doğrudan çalışma alanına atlar |

---

## 3. 🌿 Git Worktree Operasyonları

| Eylem (Action) | Varsayılan | Önerilen | Açıklama |
| :--- | :--- | :--- | :--- |
| `new_worktree` | `"prefix+shift+g"` | `"prefix+shift+g"` | Yeni bir Git worktree ve workspace oluşturur |
| `open_worktree` | *(tanımsız)* | `"prefix+o"` | Mevcut bir Git worktree'yi açar ve seçer |
| `remove_worktree` | *(tanımsız)* | `"prefix+x"` | Seçili Git worktree'yi siler/kaldırır |

---

## 4. 📑 Sekme (Tab) Yönetimi

| Eylem (Action) | Varsayılan | Açıklama |
| :--- | :--- | :--- |
| `new_tab` | `"prefix+c"` | Yeni bir sekme oluşturur |
| `rename_tab` | `"prefix+shift+t"` | Mevcut sekmeyi yeniden adlandırır |
| `close_tab` | `"prefix+shift+x"` | Mevcut sekmeyi kapatır |
| `previous_tab` | `"prefix+p"` | Önceki sekmeye geçer |
| `next_tab` | `"prefix+n"` | Sonraki sekmeye geçer |
| `switch_tab` | `"prefix+1..9"` | 1-9 arasındaki sekmeye doğrudan geçer |

---

## 5. 🪟 Panel (Pane) Bölme, Boyutlandırma ve Odaklanma

| Eylem (Action) | Varsayılan | Açıklama |
| :--- | :--- | :--- |
| `split_vertical` | `"prefix+v"` | Paneli dikey böler (yan yana) |
| `split_horizontal` | `"prefix+minus"` | Paneli yatay böler (alt alta) |
| `close_pane` | `"prefix+x"` | Aktif paneli kapatır |
| `zoom` | `"prefix+z"` | Aktif paneli tam ekran büyütür / geri küçültür |
| `resize_mode` | `"prefix+r"` | Panel boyutlandırma moduna geçer |
| `rename_pane` | `"prefix+shift+p"` | Aktif panele özel etiket/isim verir |
| `edit_scrollback` | `"prefix+e"` | Panel kaydırma geçmişini editörde açar |
| `focus_pane_left` | `"prefix+h"` | Soldaki panele odaklanır |
| `focus_pane_down` | `"prefix+j"` | Aşağıdaki panele odaklanır |
| `focus_pane_up` | `"prefix+k"` | Yukarıdaki panele odaklanır |
| `focus_pane_right` | `"prefix+l"` | Sağdaki panele odaklanır |
| `cycle_pane_next` | `"prefix+tab"` | Sonraki panele geçer |
| `cycle_pane_previous` | `"prefix+shift+tab"` | Önceki panele geçer |
| `last_pane` | *(tanımsız)* | Son kullanılan panele geri döner |

---

## 6. 🤖 AI Ajan (Agent) Takip ve Navigasyonu

| Eylem (Action) | Varsayılan | Önerilen | Açıklama |
| :--- | :--- | :--- | :--- |
| `next_agent` | *(tanımsız)* | `"prefix+j"` | Sonraki AI ajan paneline odaklanır |
| `previous_agent` | *(tanımsız)* | `"prefix+k"` | Önceki AI ajan paneline odaklanır |
| `focus_agent` | *(tanımsız)* | `"prefix+alt+1..9"` | İndeksli AI ajanına doğrudan odaklanır |
| `open_notification_target`| `"prefix+o"` | `"prefix+o"` | Bildirim gönderen ajanın paneline gider |

---

## 7. 🧭 Navigate Modu (Menü Açıkken Yerel Tuşlar)

`navigate` modu açıkken prefix tuşu gerekmeden doğrudan tek tuşla gezinme sağlar:

| Eylem (Action) | Varsayılan | Açıklama |
| :--- | :--- | :--- |
| `navigate_workspace_up` | `"up"` | Yukarıdaki çalışma alanına odaklan |
| `navigate_workspace_down` | `"down"` | Aşağıdaki çalışma alanına odaklan |
| `navigate_pane_left` | `"h"` | Soldaki panele odaklan |
| `navigate_pane_down` | `"j"` | Aşağıdaki panele odaklan |
| `navigate_pane_up` | `"k"` | Yukarıdaki panele odaklan |
| `navigate_pane_right` | `"l"` | Sağdaki panele odaklan |

---

## 8. 🚀 Özel Açılır Terminal Komutları (`[[keys.command]]`)

Örnek modal veya geçici panel komutları:

```toml
# Lazygit Yüzen Pencere
[[keys.command]]
key = "prefix+alt+g"
type = "popup"
command = "lazygit"
width = "85%"
height = "85%"

# Btop Sistem İzleyici Pop-up
[[keys.command]]
key = "prefix+alt+b"
type = "popup"
command = "btop"
width = "80%"
height = "80%"
```
