<p align="center">
  <img src="assets/logo.png" width="128" alt="d77void logo">
</p>

<h1 align="center">srcpkgs-d77</h1>

<p align="center">
  d77void srcpkgs collection.
</p>

---

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

You are now able to install the pkgs from d77void repo.
 
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
    sudo xbps-install --repository /hostdir/binpkgs/d77/ <package1> <package2> ...
    ```

</details>

<hr>

## Automated template updates

A [scheduled workflow](.github/workflows/update-templates.yml) checks every
`srcpkgs/*/template`, `cosmic/*/template` and `hyprland/*/template` against
its upstream (GitHub/Codeberg releases and tags) every 3 days and opens a pull request
when a newer version is found, bumping
`version`, resetting `revision` to `1` and refreshing `checksum` — only after
actually downloading and verifying the new source. It can also be run
on demand from the Actions tab (`workflow_dispatch`).

Not every template is eligible: packages fetched from hosts other than
GitHub/Codeberg, or pinned to a `${_commit}` hash instead of a `${version}`
tag, are left for manual updates. See the header of
[`scripts/update_templates.py`](scripts/update_templates.py) for details.

<hr>

## Credits

- [Nizarjh: blackhole-vl](https://github.com/Event-Horizon-VL/blackhole-vl): Inspiration on README file and templates for Hyprland
- [Bella109: Cosmic-repo](https://codeberg.org/Bella109/void-cosmic-repo): The whole templates for CosmicDE
- [Sofiya: hyprland-void](https://github.com/sofijacom/hyprland-void/): Some templates for Hyprland
