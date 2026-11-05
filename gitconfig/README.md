# Instructions
*This works for macOS and Linux. Not tried Windows yet.*

From the directory containing this README file, run:

```
# Backup old gitconfig
mv ~/.gitconfig ~/.gitconfig_OLD

# Create symlink
ln -s "$(pwd)/.gitconfig" ~/.gitconfig
```

Test that the gitconfig is correctly applied.
Once sure, delete the backed up gitconfig

```
rm ~/.gitconfig_OLD
```