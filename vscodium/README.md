# Setup
*This only work on Linux and with VSCodium installed via package manager (not Flatpak)*

From the directory containing this README file, run:

```
# Check if VSCodium is installed
[ -d ~/.config/VSCodium/User ] && echo "VSCodium is correctly installed" || echo "VSCodium is could not be detected"
```

If the above check passes, run the following:

```
# Backup any existing config
mv ~/.config/VSCodium/User/settings.json ~/.config/VSCodium/User/OLD_settings.json
mv ~/.config/VSCodium/User/keybindings.json ~/.config/VSCodium/User/OLD_keybindings.json

# Create symlink
ln -s "$(pwd)/settings.json" ~/.config/VSCodium/User/settings.json
ln -s "$(pwd)/keybindings.json" ~/.config/VSCodium/User/keybindings.json
```

Test in VSCodium that the settings and keybindings are correctly applied.
Once sure, delete the backed up configs

```
rm ~/.config/VSCodium/User/OLD_settings.json ~/.config/VSCodium/User/OLD_keybindings.json
```