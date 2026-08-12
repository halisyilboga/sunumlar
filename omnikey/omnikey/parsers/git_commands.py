"""Dedicated parser and comprehensive recipe catalog for Git version control commands."""

from pathlib import Path
from typing import List, Tuple

from omnikey.models import Keybinding
from omnikey.parsers.base import BaseParser
from omnikey.semantic.tagger import SemanticTagger


# Comprehensive curated Git recipes catalog
GIT_RECIPES: List[Tuple[str, str, str, List[str]]] = [
    # --- Branching & Switching (Dallar & Geçiş) ---
    (
        "git checkout -b <dal-adi>",
        "checkout",
        "Yeni dal oluştur ve hemen o dala geç / Create and switch to new branch",
        ["git", "branch", "checkout", "switch", "yeni", "dal", "olustur", "gecis", "create"],
    ),
    (
        "git switch -c <dal-adi>",
        "switch",
        "Modern komutla yeni dal oluştur ve geç / Create and switch to new branch (modern)",
        ["git", "switch", "branch", "dal", "yeni", "modern", "gecis"],
    ),
    (
        "git branch -a",
        "branch",
        "Tüm yerel ve uzak (remote) dalları listele / List all local and remote branches",
        ["git", "branch", "list", "dallar", "uzak", "remote", "hepsi", "all"],
    ),
    (
        "git branch -d <dal-adi>",
        "branch",
        "Birleştirilmiş (merged) dalı güvenle sil / Safe delete merged branch",
        ["git", "branch", "delete", "sil", "kaldir", "dal", "safe"],
    ),
    (
        "git branch -D <dal-adi>",
        "branch",
        "Birleşmemiş dalı zorla sil / Force delete unmerged branch",
        ["git", "branch", "delete", "force", "zorla", "sil", "dal"],
    ),
    (
        "git branch -m <yeni-isim>",
        "branch",
        "Mevcut dalın adını değiştir / Rename current branch",
        ["git", "branch", "rename", "adlandir", "isim", "degistir", "dal"],
    ),
    (
        "git branch --merged",
        "branch",
        "Mevcut dala birleştirilmiş dalları göster / List branches merged into current HEAD",
        ["git", "branch", "merged", "birlestirilmis", "tamamlanan"],
    ),

    # --- Staging & Commits (Sahneleme & Commit) ---
    (
        "git add -p",
        "add",
        "Değişiklikleri parça parça (hunk bazında) inceleyerek sahneye ekle / Patch interactive staging",
        ["git", "add", "patch", "parca", "hunk", "sahne", "interactive", "secerek"],
    ),
    (
        "git commit -m '<mesaj>'",
        "commit",
        "Sahnelenen değişiklikleri açıklama ile kaydet / Commit staged changes with message",
        ["git", "commit", "kaydet", "mesaj", "save"],
    ),
    (
        "git commit --amend --no-edit",
        "commit",
        "Son commiti mesajı değiştirmeden yeni değişikliklerle güncelle / Amend staged changes into last commit",
        ["git", "commit", "amend", "guncelle", "son", "ekle", "duzelt"],
    ),
    (
        "git commit --amend",
        "commit",
        "Son commitin mesajını veya içeriğini düzenle / Edit last commit message or contents",
        ["git", "commit", "amend", "duzenle", "mesaj", "edit"],
    ),

    # --- Stash Operations (Geçici Saklama) ---
    (
        "git stash push -m '<mesaj>'",
        "stash",
        "Mevcut çalışma dizinindeki değişiklikleri etiketle sakla / Stash working directory with message",
        ["git", "stash", "sakla", "gecici", "kaydet", "save", "push"],
    ),
    (
        "git stash list",
        "stash",
        "Saklanan tüm stash kayıtlarını listele / List all stash entries",
        ["git", "stash", "list", "saklananlar", "gecmis", "kayitlar"],
    ),
    (
        "git stash pop",
        "stash",
        "En son saklanan stash'i geri yükle ve listeden kaldır / Apply latest stash and drop from list",
        ["git", "stash", "pop", "geri-al", "uygula", "cikar", "yukle"],
    ),
    (
        "git stash apply stash@{0}",
        "stash",
        "Belirtilen stash'i silmeden çalışma alanına uygula / Apply specific stash without removing",
        ["git", "stash", "apply", "uygula", "sakla", "koru"],
    ),
    (
        "git stash show -p stash@{0}",
        "stash",
        "Stash içeriğindeki diff farklarını incele / View diff of specific stash",
        ["git", "stash", "show", "diff", "incele", "fark"],
    ),
    (
        "git stash drop stash@{0}",
        "stash",
        "Belirtilen stash kaydını listeden sil / Delete specific stash entry",
        ["git", "stash", "drop", "sil", "kaldir", "delete"],
    ),
    (
        "git stash clear",
        "stash",
        "Tüm stash geçmişini tamamen temizle / Remove all stash entries",
        ["git", "stash", "clear", "temizle", "hepsini-sil"],
    ),

    # --- Undo & Disaster Recovery (Geri Alma & Kurtarma) ---
    (
        "git reflog",
        "reflog",
        "HEAD hareket geçmişini göster (Kayıp/silinmiş commitleri kurtar) / Show reference logs for disaster recovery",
        ["git", "reflog", "kurtar", "recover", "kayip", "gecmis", "undo", "head"],
    ),
    (
        "git reset --soft HEAD~1",
        "reset",
        "Son commiti geri al ama değişiklikleri sahnelenmiş (staged) tut / Undo commit keeping staged changes",
        ["git", "reset", "soft", "geri-al", "commit", "staged", "sahne"],
    ),
    (
        "git reset --mixed HEAD~1",
        "reset",
        "Son commiti geri al, değişiklikleri çalışma dizininde tut (Unstage) / Undo commit keeping unstaged files",
        ["git", "reset", "mixed", "geri-al", "unstage", "calisma"],
    ),
    (
        "git reset --hard HEAD~1",
        "reset",
        "Son commiti ve tüm yerel değişiklikleri tamamen yok et / Completely discard last commit and changes",
        ["git", "reset", "hard", "yok-et", "sil", "temizle", "discard"],
    ),
    (
        "git restore <dosya>",
        "restore",
        "Dosyadaki kaydedilmemiş yerel değişiklikleri geri al / Discard unstaged changes in working file",
        ["git", "restore", "geri-al", "dosya", "discard", "iptal"],
    ),
    (
        "git restore --staged <dosya>",
        "restore",
        "Dosyayı sahneden çıkar (Unstage) / Remove file from staging area",
        ["git", "restore", "staged", "unstage", "sahne", "cikar"],
    ),
    (
        "git revert <commit-hash>",
        "revert",
        "Commitin tersini yeni bir commit olarak uygulayarak güvenle geri al / Revert commit safely with new commit",
        ["git", "revert", "geri-al", "guvenli", "safe", "commit"],
    ),
    (
        "git clean -fd",
        "clean",
        "Takip edilmeyen (untracked) tüm dosya ve klasörleri temizle / Force clean untracked files and directories",
        ["git", "clean", "temizle", "untracked", "dosyalar", "sil"],
    ),

    # --- Rebase & History Rewriting (Tarihçe Düzenleme) ---
    (
        "git rebase -i HEAD~<N>",
        "rebase",
        "Son N commiti interaktif düzenle veya birleştir (Squash/Fixup) / Interactive rebase to squash or edit",
        ["git", "rebase", "interactive", "squash", "fixup", "birlestir", "tarihce", "duzenle"],
    ),
    (
        "git rebase --continue",
        "rebase",
        "Rebase çakışmalarını çözdükten sonra süreci devam ettir / Continue rebase after resolving conflicts",
        ["git", "rebase", "continue", "devam", "cözüm", "cakisma"],
    ),
    (
        "git rebase --abort",
        "rebase",
        "Çakışan rebase işlemini iptal et ve önceki duruma dön / Abort in-progress rebase and restore HEAD",
        ["git", "rebase", "abort", "iptal", "vazgec", "don"],
    ),
    (
        "git pull --rebase origin <dal-adi>",
        "pull",
        "Uzak daldaki değişiklikleri rebase ile yerel commitlerin arkasına al / Fetch and rebase local commits on remote",
        ["git", "pull", "rebase", "guncelle", "cek", "origin"],
    ),

    # --- Cherry-Pick & Merging (Seçici Alma & Birleştirme) ---
    (
        "git cherry-pick <commit-hash>",
        "cherry-pick",
        "Başka daldaki belirli bir commiti mevcut dala uygula / Apply specific commit from another branch",
        ["git", "cherry-pick", "al", "sec", "uygula", "commit", "aktar"],
    ),
    (
        "git cherry-pick --abort",
        "cherry-pick",
        "Çakışan cherry-pick işlemini iptal et / Abort current cherry-pick",
        ["git", "cherry-pick", "abort", "iptal", "vazgec"],
    ),
    (
        "git merge --no-ff <dal-adi>",
        "merge",
        "Dalı fast-forward yapmadan açık merge commiti ile birleştir / Merge branch with explicit merge commit",
        ["git", "merge", "birlestir", "no-ff", "dal", "branch"],
    ),
    (
        "git merge --abort",
        "merge",
        "Çakışan birleştirme (merge) işlemini iptal et / Abort in-progress merge",
        ["git", "merge", "abort", "iptal", "vazgec", "cakisma"],
    ),

    # --- Git Worktrees (İzole Çalışma Alanları) ---
    (
        "git worktree add <dizin-yolu> <dal-adi>",
        "worktree",
        "Farklı bir dizinde bağımsız paralel çalışma alanı aç / Create isolated working tree in new directory",
        ["git", "worktree", "add", "yeni", "dizin", "paralel", "calisma-alani", "dal"],
    ),
    (
        "git worktree list",
        "worktree",
        "Mevcut tüm Git worktree çalışma alanlarını listele / List active Git worktree instances",
        ["git", "worktree", "list", "alanlar", "dizinler", "aktif"],
    ),
    (
        "git worktree remove <dizin-yolu>",
        "worktree",
        "Tamamlanan worktree çalışma alanını güvenle sil / Remove and deregister Git worktree",
        ["git", "worktree", "remove", "sil", "kaldir", "dizin"],
    ),
    (
        "git worktree prune",
        "worktree",
        "Silinmiş dizinlerin worktree referanslarını temizle / Prune stale worktree metadata",
        ["git", "worktree", "prune", "temizle", "eski"],
    ),

    # --- Inspection, Log, Diff & Bisect (İnceleme & Hata Avı) ---
    (
        "git log --graph --oneline --decorate --all",
        "log",
        "Tüm dalların commit tarihçesini grafiksel ve tek satırda görselleştir / Graph visual commit log",
        ["git", "log", "graph", "gorsel", "agac", "tarihce", "oneline", "all"],
    ),
    (
        "git log -S '<metin>'",
        "log",
        "Belirtilen metnin eklendiği veya silindiği commitleri bul (Pickaxe) / Search commits by code changes",
        ["git", "log", "search", "ara", "kod", "metin", "pickaxe", "bul"],
    ),
    (
        "git log -p <dosya>",
        "log",
        "Dosyanın tüm commit geçmişini satır satır diff farklarıyla listele / Show file history with diffs",
        ["git", "log", "diff", "dosya", "tarihce", "farklar"],
    ),
    (
        "git diff",
        "diff",
        "Çalışma alanındaki sahnelenmemiş (unstaged) değişiklikleri göster / Show unstaged working changes",
        ["git", "diff", "fark", "degisiklik", "unstaged"],
    ),
    (
        "git diff --staged",
        "diff",
        "Sahneye eklenen (staged) commit öncesi değişiklikleri göster / Show staged changes ready to commit",
        ["git", "diff", "staged", "sahne", "fark", "incele"],
    ),
    (
        "git diff <dal1>..<dal2>",
        "diff",
        "İki dal arasındaki tüm kod farklarını karşılaştır / Compare diff between two branches",
        ["git", "diff", "karsilastir", "dallar", "fark", "compare"],
    ),
    (
        "git blame -L <bas>,<bit> <dosya>",
        "blame",
        "Dosyadaki belirli satırları kimin ne zaman yazdığını göster / Show author and commit for lines",
        ["git", "blame", "yazar", "satir", "kim", "author", "tarih"],
    ),
    (
        "git bisect start && git bisect bad && git bisect good <commit>",
        "bisect",
        "İkili arama (binary search) ile regresyon hatasının başladığı commiti bul / Bisect to find breaking commit",
        ["git", "bisect", "hata", "avla", "bul", "binary-search", "bug", "regresyon"],
    ),
    (
        "git bisect reset",
        "bisect",
        "Hata arama modundan çık ve normal HEAD durumuna dön / End bisect session and restore state",
        ["git", "bisect", "reset", "bitir", "cikis"],
    ),

    # --- Remotes, Submodules & Tags (Uzak Depo & Etiketler) ---
    (
        "git remote -v",
        "remote",
        "Bağlı uzak depoların (remote) adreslerini listele / List configured remote repositories",
        ["git", "remote", "adres", "origin", "upstream", "list"],
    ),
    (
        "git remote add upstream <url>",
        "remote",
        "Orijinal açık kaynak depoyu 'upstream' olarak ekle / Add upstream repository remote",
        ["git", "remote", "add", "upstream", "ekle", "bagla"],
    ),
    (
        "git fetch --all --prune",
        "fetch",
        "Tüm uzak depoları çek ve silinmiş dalları yerelden temizle / Fetch remotes and prune deleted branches",
        ["git", "fetch", "prune", "guncelle", "temizle", "hepsi"],
    ),
    (
        "git push origin --force-with-lease",
        "push",
        "Güvenli zorla gönderme (başkalarının commitini ezmeden zorla push) / Safe force push without overwriting teammates",
        ["git", "push", "force", "force-with-lease", "guvenli", "gonder"],
    ),
    (
        "git tag -a v1.0.0 -m '<mesaj>'",
        "tag",
        "Açıklamalı (annotated) sürüm etiketi oluştur / Create annotated version release tag",
        ["git", "tag", "versiyon", "surum", "etiket", "release", "v1"],
    ),
    (
        "git push origin --tags",
        "tag",
        "Tüm yerel versiyon etiketlerini uzak depoya gönder / Push all local tags to remote repository",
        ["git", "push", "tags", "etiketler", "gonder", "surumler"],
    ),
    (
        "git submodule update --init --recursive",
        "submodule",
        "Tüm alt modülleri (submodules) indir ve başlat / Initialize and clone all submodules recursively",
        ["git", "submodule", "alt-modul", "update", "init", "recursive", "klonla"],
    ),
]


class GitCommandsParser(BaseParser):
    """Parses and delivers built-in Git recipes and version control standards."""

    @property
    def tool_name(self) -> str:
        return "git"

    def can_handle(self, file_path: Path) -> bool:
        return False

    def parse(self, file_path: Path) -> List[Keybinding]:
        return []

    @classmethod
    def get_all_git_recipes(cls) -> List[Keybinding]:
        """Return full catalog of Git command recipes and workflows."""
        results: List[Keybinding] = []
        for combo, action, desc, custom_tags in GIT_RECIPES:
            tags = SemanticTagger.generate_tags(
                tool="git",
                key_combo=combo,
                action_raw=action,
                description=desc,
                mode="cli",
            )
            tags.extend(["git", "vcs", "version-control", "komut", "cli", "terminal"])
            tags.extend(custom_tags)
            clean_tags = sorted(list(set(t.strip().lower() for t in tags if len(t.strip()) >= 2)))

            results.append(
                Keybinding(
                    tool="git",
                    key_combo=combo,
                    action_raw=action,
                    description=desc,
                    source_file="builtin://git_recipes",
                    mode="cli",
                    tags=clean_tags,
                )
            )
        return results
