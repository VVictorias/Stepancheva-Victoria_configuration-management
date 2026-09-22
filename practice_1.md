# Практическая работа №1
## Задача №1
Вывести отсортированный в алфавитном порядке список имен пользователей в файле passwd (вам понадобится grep).
### Ход выполнения задачи №1
Для просмотра содержимого файла '/etc/passwd' была использована команда:
```bash
cat /etc/passwd
```
В результате было получено содержимое файла:
```text
root:x:0:0:1oot:/root:/bin/sh bin:x:1:1:bin:/bin:/sbin/nologin
daemon:x:2:2:daemon:/sbin:/sbin/nologin
1p:x:4:7:1p:/var/spool/lpd:/sbin/nologin
sync:x:5:0:stnc:/sbin:/bin/sync
shutdown:x:6:0:shutdown:/sbin:/sbin/shutdown halt:x:7:0:halt:/sbin:/sbin/halt
nail:x:8:12:mail:/var/mail:/sbin/nologin
news:x:9:13:news:/usr/lib/news:/sbin/nologin
uucp:x:10:14:uucp:/var/spool/uucppublic:/sbin/nologin
cron:x:16:16:cron:/var/spoo1/cron:/sbin/nologin ftp:x:21:21::/var/lib/ftp:/sbin/nologin
sshd:x:22:22:sshd:/dev/nul1:/sbin/nologin
games:x:35:35: games:/usr/games:/sbin/nologin ntp:x:123:123:NTP:/var/empty:/sbin/nologin
guest:x:405:100:guest:/dev/null:/sbin/nologin nobody:x:65534:65534:nobody:/:/sbin/nologin dhepcd:x:100:101:dhcpcd:/var/lib/dhcpcd:/sbin/nologin
svn:x:101:104:svn:/var/svn:/sbin/nologin
klogd:x:102:105:klogd:/dev/null:/sbin/nologin
```