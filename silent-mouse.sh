#!/bin/bash

# Check which version you're using
echo
echo "---------------------------------------------------------------------------"
cd ~
upower --version
UPOWER_ORIG_VER=`upower --version`

# Check Debian / Ubuntu vs. Arch Linux / Manjaro
OS=`awk -F= '/^ID=/{print $2}' /etc/os-release`
OS_VER=`awk -F= '/^VERSION_ID=/{print $2}' /etc/os-release | cut -d "\"" -f 2`
echo "---------------------------------------------------------------------------"
echo
echo

if [[ "$OS" == "manjaro" ]]
then
    echo "Manjaro detected"
    sudo pacman -S base-devel gtk-doc gobject-introspection git
    PATH_UPOWERD="/usr/lib"
    PATH_UPOWER="/usr/bin"
elif [[ "$OS" == "ubuntu" ]]
then
    sudo apt install git gtk-doc-tools gobject-introspection libgudev-1.0-dev libusb-1.0-0-dev autoconf libtool autopoint
    if [[ "$OS_VER" == "20.10" ]]
    then
        echo "Ubuntu version 20.10 (Groovy Gorilla) detected"
        PATH_UPOWERD="/usr/libexec"
        PATH_UPOWER="/usr/bin"
    else
        echo "Ubuntu version <= 20.04 detected"
        PATH_UPOWERD="/usr/lib/upower"
        PATH_UPOWER="/usr/bin"
    fi
else
    echo "Unknown system; this script was only tested on ubuntu and manjaro."
    exit 1
fi

# Download and patch upowerd
#
git clone https://gitlab.freedesktop.org/upower/upower
cd upower/src
wget https://gist.githubusercontent.com/guiambros/f2bf07f1cc085f8f0b0a9e04c0a767b4/raw/ef90dfcfa2489bab577bd984a6082abacdf8b0b1/up-device.patch  
patch < up-device.patch
cd ..
./autogen.sh
./configure
make

# Install upowerd
#
CUR_DATETIME=`date +%Y-%m-%d-%H%M%S`

pushd .
cd src/.libs
strip upowerd
sudo chown root.root upowerd
sudo mv upowerd ${PATH_UPOWERD}/upowerd-silent
cd ${PATH_UPOWERD}
sudo mv upowerd upowerd-original-${CUR_DATETIME}
sudo ln -s upowerd-silent upowerd
popd

# Install upower
#
pushd .
cd tools/.libs
strip upower
sudo chown root.root upower
sudo mv upower ${PATH_UPOWER}/upower-silent
cd ${PATH_UPOWER}
sudo mv upower upower-original-${CUR_DATETIME}
sudo ln -s upower-silent upower
popd

# Restart upowerd
#
sudo systemctl restart upower

# Compare versions before/after (they will likely be different, but it depends on what your distro packages by default)
echo
echo "---------------------------------------------------------------------------"
echo "upower version BEFORE the update:"
echo "${UPOWER_ORIG_VER}"
echo "-------------------------------------"
echo "upower version AFTER the update:"
upower --version
