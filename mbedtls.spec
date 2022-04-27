%global optflags %{optflags} -O3 -Wno-error=unused-but-set-parameter -Wno-error=unknown-warning-option

# (tpg) enable PGO build
%bcond_without pgo

%define major 2
%define libname %mklibname %{name} %{major}
%define clibname %mklibname mbedcrypto %{major}
%define xlibname %mklibname mbedx509 %{major}
%define devname %mklibname %{name} -d

Summary:	An SSL library
Name:		mbedtls
Version:	2.28.0
Release:	1
License:	Apache 2.0
Group:		System/Libraries
Url:		https://tls.mbed.org
# This is the official download location...
# Source0:	https://tls.mbed.org/download/mbedtls-%{version}-apache.tgz
# Sometimes newer versions can be found here - but they appear to be
# unsupported interim releases on the way to a new branch
Source0:	https://github.com/ARMmbed/mbedtls/archive/v%{version}/mbedtls-%{version}.tar.gz

BuildRequires:	cmake
BuildRequires:	ninja
BuildRequires:	doxygen
BuildRequires:	graphviz
BuildRequires:	pkgconfig(libcrypto)
BuildRequires:	pkgconfig(libpkcs11-helper-1)
BuildRequires:	pkgconfig(zlib)

%description
mbed TLS (formerly PolarSSL) is an SSL library written in ANSI C.
It makes it easy for developers to include cryptographic and
SSL/TLS capabilities in their (embedded) products with as little
hassle as possible. It is designed to be readable, documented,
tested, loosely coupled and portable.

This package contains mbed TLS programs.

%files
%{_bindir}/*
%doc ChangeLog
%license LICENSE

#----------------------------------------------------------------------------

%package -n %{libname}
Summary:	mbed TLS library
Group:		System/Libraries

%description -n %{libname}
mbed TLS (formerly PolarSSL) is an SSL library written in ANSI C.
It makes it easy for developers to include cryptographic and SSL/TLS
capabilities in their (embedded) products with as little hassle as
possible. It is designed to be readable, documented, tested, loosely
coupled and portable.

This package contains the library itself.

%files -n %{libname}
%{_libdir}/libmbedtls.so.%{major}*
%{_libdir}/libmbedtls.so.1*

#----------------------------------------------------------------------------

%package -n %{clibname}
Summary:	mbed TLS Crypto library
Group:		System/Libraries

%description -n %{clibname}
mbed TLS (formerly PolarSSL) is an SSL library written in ANSI C.
It makes it easy for developers to include cryptographic and SSL/TLS
capabilities in their (embedded) products with as little hassle as
possible. It is designed to be readable, documented, tested, loosely
coupled and portable.

This package contains the library itself.

%files -n %{clibname}
%{_libdir}/libmbedcrypto.so.{major}.*

#----------------------------------------------------------------------------

%package -n %{xlibname}
Summary:	mbed TLS X.509 library
Group:		System/Libraries

%description -n %{xlibname}
mbed TLS (formerly PolarSSL) is an SSL library written in ANSI C.
It makes it easy for developers to include cryptographic and SSL/TLS
capabilities in their (embedded) products with as little hassle as
possible. It is designed to be readable, documented, tested, loosely
coupled and portable.

This package contains the library itself.

%files -n %{xlibname}
%{_libdir}/libmbedx509.so.*

#----------------------------------------------------------------------------

%package -n %{devname}
Summary:	mbed TLS development files
Group:		Development/C
Requires:	%{libname} = %{EVRD}
Requires:	%{clibname} = %{EVRD}
Requires:	%{xlibname} = %{EVRD}
Provides:	mbedtls-devel = %{EVRD}
Provides:	polarssl-devel = %{EVRD}

%description -n %{devname}
mbed TLS (formerly PolarSSL) is an SSL library written in ANSI C.
It makes it easy for developers to include cryptographic and SSL/TLS
capabilities in their (embedded) products with as little hassle as
possible.

It is designed to be readable, documented, tested, loosely coupled
and portable.

This package contains development files.

%files -n %{devname}
%{_includedir}/%{name}
%{_includedir}/psa
%{_libdir}/lib%{name}.so
%{_libdir}/libmbedcrypto.so
%{_libdir}/libmbedx509.so
%doc apidoc
%license LICENSE

#----------------------------------------------------------------------------

%prep
%autosetup -p1

enable_mbedtls_option() {
    local myopt="$@"
    # check that config.h syntax is the same at version bump
    sed -i \
        -e "s://#define ${myopt}:#define ${myopt}:" \
        include/mbedtls/config.h || die
}

enable_mbedtls_option POLARSSL_ZLIB_SUPPORT
enable_mbedtls_option POLARSSL_HAVEGE_C

%build
%ifarch %{ix86}
# Needed because of strange inline ASM constructs
# clang doesn't parse
export CC=gcc
export CXX=g++
%endif

%if %{with pgo}
export LD_LIBRARY_PATH="$(pwd)"

CFLAGS="%{optflags} -fprofile-generate" \
CXXFLAGS="%{optflags} -fprofile-generate" \
LDFLAGS="%{build_ldflags} -fprofile-generate" \
%cmake \
	-DMBEDTLS_PYTHON_EXECUTABLE=%{_bindir}/python \
	-DUSE_SHARED_MBEDTLS_LIBRARY:BOOL=ON \
	-DUSE_STATIC_MBEDTLS_LIBRARY:BOOL=OFF \
	-DENABLE_PROGRAMS:BOOL=ON \
	-DENABLE_TESTING:BOOL=ON \
	-DENABLE_ZLIB_SUPPORT:BOOL=ON \
	-DUSE_PKCS11_HELPER_LIBRARY:BOOL=ON \
	-DLINK_WITH_PTHREAD:BOOL=ON \
	-G Ninja

%ninja_build

LD_PRELOAD="./build/library/libmbedcrypto.so ./build/library/libmbedx509.so ./build/library/libmbedtls.so ./build/library/libmbedcrypto.so.7" %ninja_test || (cat Testing/Temporary/LastTest.log && exit 1)

unset LD_LIBRARY_PATH
llvm-profdata merge --output=%{name}-llvm.profdata $(find . -type f -name "*.profraw")
PROFDATA="$(realpath %{name}-llvm.profdata)"
rm -f *.profraw
ninja clean

CFLAGS="%{optflags} -fprofile-use=$PROFDATA" \
CXXFLAGS="%{optflags} -fprofile-use=$PROFDATA" \
LDFLAGS="%{build_ldflags} -fprofile-use=$PROFDATA" \
%endif
%cmake \
	-DMBEDTLS_PYTHON_EXECUTABLE=%{_bindir}/python \
	-DUSE_SHARED_MBEDTLS_LIBRARY:BOOL=ON \
	-DUSE_STATIC_MBEDTLS_LIBRARY:BOOL=OFF \
	-DENABLE_PROGRAMS:BOOL=ON \
	-DENABLE_TESTING:BOOL=ON \
	-DENABLE_ZLIB_SUPPORT:BOOL=ON \
	-DUSE_PKCS11_HELPER_LIBRARY:BOOL=ON \
	-DLINK_WITH_PTHREAD:BOOL=ON \
	-G Ninja

%ninja_build

# doc
%ninja_build apidoc

%install
%ninja_install -C build

# fix files name
for file in benchmark
do
    mv %{buildroot}%{_bindir}/${file} %{buildroot}%{_bindir}/${file}.mbedtls
done
