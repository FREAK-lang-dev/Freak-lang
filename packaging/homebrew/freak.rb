class Freak < Formula
  desc "FREAK programming language compiler and package manager"
  homepage "https://github.com/FREAK-lang-dev/Freak-lang"
  version "0.13.3"
  license "MIT"

  on_macos do
    on_arm do
      url "https://github.com/FREAK-lang-dev/Freak-lang/releases/download/v#{version}/freak-macos-arm64.tar.gz"
      sha256 "HOMEBREW_SHA256_MACOS_ARM64_PLACEHOLDER"
    end
    # Note: no macOS x64 release — only arm64 (Apple Silicon) is supported.
  end

  on_linux do
    on_arm do
      url "https://github.com/FREAK-lang-dev/Freak-lang/releases/download/v#{version}/freak-linux-arm64.tar.gz"
      sha256 "HOMEBREW_SHA256_LINUX_ARM64_PLACEHOLDER"
    end

    on_intel do
      url "https://github.com/FREAK-lang-dev/Freak-lang/releases/download/v#{version}/freak-linux-x64.tar.gz"
      sha256 "HOMEBREW_SHA256_LINUX_X64_PLACEHOLDER"
    end
  end

  def install
    # Install real binaries into lib/freak/bin/ so the shims can exec them.
    (lib/"freak/bin").install "freak/bin/freak"
    (lib/"freak/bin").install "freak/bin/hangar"

    # Ship the runtime and standard library alongside the binaries.
    # The compiler reads FREAK_HOME at build time to locate these.
    (lib/"freak/runtime").install Dir["freak/runtime/*"]
    (lib/"freak/std").install Dir["freak/std/*"]

    # Write thin shims to bin/ that set FREAK_HOME before exec-ing the real binary.
    freak_home = lib/"freak"
    %w[freak hangar].each do |cmd|
      (bin/cmd).write <<~SH
        #!/bin/sh
        export FREAK_HOME="${FREAK_HOME:-#{freak_home}}"
        exec "#{lib}/freak/bin/#{cmd}" "$@"
      SH
      (bin/cmd).chmod 0755
    end
  end

  test do
    system "#{bin}/freak", "version"
    system "#{bin}/hangar", "version"

    # Write and compile a minimal hello-world program.
    (testpath/"hello.fk").write <<~FK
      @protagonist
      task main() {
        say "hello from homebrew test"
      }
    FK
    system "#{bin}/freak", "build", "#{testpath}/hello.fk"
  end
end
