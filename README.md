## ESP32 setup:

Add user to dialout group:

    sudo usermod -aG dialout $USER
    sudo reboot

The CH340 serial driver for the ESP32 is not included in the JetPack 6.x kernel, so it needs to be installed manually. Here’s how:

    git clone https://github.com/juliagoda/CH341SER.git
    cd CH341SER
    make
    sudo make install
    sudo insmod ./ch34x.ko

To make it persistent, add it to the kernel:

    sudo cp ch34x.ko /lib/modules/$(uname -r)/kernel/drivers/usb/serial/
    sudo depmod -a
    sudo bash -c 'echo "ch34x" >> /etc/modules'
