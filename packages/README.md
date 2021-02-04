## Packages
### Description
These packages are special in the sense that these are nopkg packages that have unique properties.


#### CommandLineTools
This package is able to detect wether commandline tools are installed and can silently install then when required.
#### Homebrew
This package can install Homebrew for the currently logged in user without user interaction.
#### XcodeFirstLaunch
Xcode does needs admin permissions on first start after install/update. This package will detect this and automatically install the required software. It is recommended to queue this item as update for an Xcode installation.
#### DownloadMacOS
This package can download the macOS version given in the version key directly from the Apple CDN bypassing the need to upload the OS every time there is a new release. This package supports deep insights into the status of the download (progress bar, status messages) by leveraging native munki functions (see screenshot).

These keys are used for logic:
- version: Downloads this specific version
- display_name: Used as title for the updates tab
- name: Must be "DownloadMacOS" so that the script can extract the info above

![CatalogReporter Preview](../SamplePictures/DownloadMacOS.png)