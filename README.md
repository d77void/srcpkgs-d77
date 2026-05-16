# d77void srcpkgs collection

> [!NOTE]
> This project is **not affiliated with or endorsed by the Void Linux project** or its maintainers.
>
> Use at your own discretion.

## Overview
A collection of template files for building packages on Void Linux with `xbps-src`.

This repository provides:

- **fully working templates without binaries**

- **for full binaries** do this:

```
sudo touch /etc/xbps.d/d77void.conf
su
echo "repository=https://sourceforge.net/projects/d77void/files/d77void-repo" >> /etc/xbps.d/d77void.conf
```
Update the system and accept repo key.

you are now able to install the pkgs from d77void repo.
 
<hr>

## Installation

Currently packages are tested on the following architectures:
- x86_64

<details>
<summary><b> Manually building </b></summary>


1. Clone both this repository and [void-packages](https://github.com/void-linux/void-packages):

    ```
    git clone https://github.com/d77void/srcpkgs-d77
    git clone https://github.com/void-linux/void-packages.git
    ```

2. Copy the template files into `void-packages`:

    ```
    cp -r --remove-destination srcpkgs-d77/srcpkgs/* void-packages/srcpkgs/
    ```

3. Bootstrap the build system:

    ```
    ./xbps-src binary-bootstrap
    ```

4. Build the desired packages:

    ```
    ./xbps-src pkg <package1> <package2> ...
    ```

5. Install the built packages:

    ```
    sudo xbps-install --repository /hostdir/binpkgs/ <package1> <package2> ...
    ```

</details>

<hr>

## Credits

- [Nizarjh: blackhole-vl](https://github.com/Event-Horizon-VL/blackhole-vl): Inspiration on README file

